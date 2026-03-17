const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';
const DEFAULT_CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

function parseArgs(argv) {
  const args = { baseUrl: DEFAULT_BASE_URL, output: '', headless: true };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--base-url' && argv[i + 1]) {
      args.baseUrl = argv[++i].replace(/\/$/, '');
    } else if (arg === '--output' && argv[i + 1]) {
      args.output = argv[++i];
    } else if (arg === '--headed') {
      args.headless = false;
    }
  }
  return args;
}

function chromePath() {
  return process.env.MOREAU_PLAYWRIGHT_EXECUTABLE || DEFAULT_CHROME;
}

function basePetState(now) {
  return [
    {
      name: 'Shkodik',
      animal: 'panther',
      level: 6,
      xp: 220,
      mood: 'restless',
      base_stats: { hp: 15, atk: 16, spd: 15, wil: 10 },
      fights: [{ opponent: 'GreedyAgent', result: 'win', ticks: 14 }],
      fights_won: 3,
      fights_lost: 1,
      mutations: ['iron_marrow'],
      lab_mutations: { L3: { name: 'Iron Marrow', stat: 'hp' } },
      corruption: 18,
      instability: 4,
      deceased: false,
      is_alive: true,
      needs: { hunger: 70, health: 80, morale: 65, energy: 70, last_checked: now - 1000 },
      breed_count: 0
    },
    {
      name: 'Murka',
      animal: 'fox',
      level: 5,
      xp: 150,
      mood: 'alert',
      base_stats: { hp: 10, atk: 8, spd: 9, wil: 5 },
      fights: [{ opponent: 'RandomAgent', result: 'loss', ticks: 17 }],
      fights_won: 1,
      fights_lost: 2,
      mutations: [],
      lab_mutations: {},
      corruption: 0,
      instability: 0,
      deceased: false,
      is_alive: true,
      needs: { hunger: 60, health: 90, morale: 55, energy: 60, last_checked: now - 1000 },
      breed_count: 0
    },
    {
      name: 'Ghostik',
      animal: 'bear',
      level: 4,
      xp: 80,
      mood: 'silent',
      base_stats: { hp: 11, atk: 7, spd: 3, wil: 3 },
      fights: [{ opponent: 'Pit', result: 'loss', ticks: 11 }],
      fights_won: 0,
      fights_lost: 3,
      deceased: true,
      is_alive: false,
      death_cause: 'pit',
      death_timestamp: new Date(now - 86400000).toISOString()
    }
  ];
}

function standardStorage(now) {
  return {
    moreau_onboarding_complete: 'true',
    moreau_help_seen: 'true',
    moreau_pets: JSON.stringify(basePetState(now)),
    moreau_active_pet: '0',
    moreau_dreams: JSON.stringify({
      dreams: [{ text: 'A rusted gate opened toward black water.', read: false, type: 'prophecy', timestamp: new Date(now).toISOString() }],
      unread_count: 1
    }),
    moreau_confessions: JSON.stringify([{ text: 'I wanted another win more than I wanted sleep.' }]),
    moreau_eggs: JSON.stringify([{ species: 'chimera', parents: ['Shkodik', 'Ghostik'], incubation_end: new Date(now - 60000).toISOString(), hatched: false }]),
    moreau_genesis: JSON.stringify({
      marks: 1,
      totalResets: 0,
      allTimeDeaths: 4,
      allTimeFights: 0,
      allTimeSpecies: ['panther', 'fox', 'bear'],
      chimeraSources: ['panther', 'bear'],
      geneticMemory: 1,
      journalUnlocked: [],
      genesisExclusive: false,
      resetHistory: []
    }),
    moreau_spirit_bonds: JSON.stringify({ petName: 'Shkodik', spirits: [{ name: 'Ghostik', animal: 'bear', value: 2, stat: 'atk' }] })
  };
}

async function makePage(browser, localStorageValues) {
  const context = await browser.newContext();
  await context.addInitScript((vals) => {
    for (const [key, value] of Object.entries(vals)) localStorage.setItem(key, value);
  }, localStorageValues);
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.stack || String(error)));
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  return { context, page, pageErrors, consoleErrors };
}

async function scenario(name, fn) {
  try {
    return { name, ok: true, ...(await fn()) };
  } catch (error) {
    return { name, ok: false, error: String(error) };
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function clickFirstEnabled(locator) {
  return locator.evaluateAll((elements) => {
    for (const element of elements) {
      if (!element || !(element instanceof HTMLElement)) continue;
      if (element.classList.contains('disabled')) continue;
      if (element.offsetParent === null) continue;
      element.click();
      return true;
    }
    return false;
  });
}

async function runSuite(baseUrl, headless) {
  const now = Date.now();
  const browser = await chromium.launch({ headless, executablePath: chromePath() });
  const results = [];

  results.push(await scenario('home_first_visit_redirect', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, {});
    await page.goto(baseUrl + '/island/home', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const url = page.url();
    assert(url.endsWith('/island/onboarding'), 'fresh user should redirect to /island/onboarding');
    await context.close();
    return { url, pageErrors, consoleErrors };
  }));

  results.push(await scenario('home_chronicler', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/home', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#chroniclerConsultBtn');
    await page.click('#chroniclerConsultBtn');
    await page.waitForSelector('#chroniclerDismissBtn');
    const text = await page.locator('#chroniclerArea').innerText();
    assert(/A reading, nothing more/.test(text), 'chronicler did not render reading state');
    await context.close();
    return { text, pageErrors, consoleErrors };
  }));

  results.push(await scenario('dreams', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/dreams', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#dreamContent .dream-card');
    await page.click('#dreamContent .dream-card');
    const content = await page.locator('#dreamContent').innerText();
    assert(/THE DREAM/.test(content), 'dream card did not expand correctly');
    await context.close();
    return { content: content.slice(0, 240), pageErrors, consoleErrors };
  }));

  results.push(await scenario('train', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/train', { waitUntil: 'domcontentloaded' });
    await page.click('.opponent-card[data-opponent="greedy"]');
    await page.click('.fight-btn');
    await page.waitForTimeout(2500);
    const body = await page.locator('body').innerText();
    assert(/Series score:/.test(body), 'train fight did not finish with a result screen');
    await context.close();
    return { snippet: body.slice(0, 300), pageErrors, consoleErrors };
  }));

  results.push(await scenario('caretaker_feed', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/caretaker', { waitUntil: 'domcontentloaded' });
    await page.click('#actFeed');
    await page.waitForTimeout(600);
    const body = await page.locator('body').innerText();
    assert(/has been fed/.test(body), 'caretaker feed action did not execute');
    await context.close();
    return { snippet: body.slice(0, 260), pageErrors, consoleErrors };
  }));

  results.push(await scenario('lab_gate', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/lab', { waitUntil: 'domcontentloaded' });
    const body = await page.locator('body').innerText();
    assert(/You must be signed in to enter the laboratory/.test(body), 'lab gate text missing');
    await context.close();
    return { snippet: body.slice(0, 200), pageErrors, consoleErrors };
  }));

  results.push(await scenario('rivals', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/rivals', { waitUntil: 'domcontentloaded' });
    const body = await page.locator('body').innerText();
    assert(/Your Rivals/.test(body), 'rivals page did not render');
    await context.close();
    return { snippet: body.slice(0, 240), pageErrors, consoleErrors };
  }));

  results.push(await scenario('pit', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/pit', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.pet-pick-card[data-side="left"]');
    const pickedLeft = await clickFirstEnabled(page.locator('.pet-pick-card[data-side="left"]'));
    assert(pickedLeft, 'pit left side had no enabled cards');
    const pickedRight = await clickFirstEnabled(page.locator('.pet-pick-card[data-side="right"]'));
    assert(pickedRight, 'pit right side had no enabled cards after left selection');
    await page.click('.fight-btn');
    await page.waitForTimeout(2200);
    const body = await page.locator('body').innerText();
    assert(/VICTORY|DEFEAT|winner/i.test(body), 'pit fight did not produce a result');
    await context.close();
    return { snippet: body.slice(0, 280), pageErrors, consoleErrors };
  }));

  results.push(await scenario('ecology', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/ecology', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#startRunBtn');
    await page.waitForSelector('#seasonValue');
    await page.click('#startRunBtn');
    await page.waitForTimeout(400);
    const seasonValue = await page.locator('#seasonValue').innerText();
    assert(/s1|first-descent/i.test(seasonValue), 'ecology season value did not render');
    await page.selectOption('#queueActionSelect', 'CARE');
    await page.click('#enqueueBtn');
    await page.waitForTimeout(400);
    await page.click('#tickOnceBtn');
    await page.waitForTimeout(1000);
    const queueBody = await page.locator('#queueArea').innerText();
    assert(!/CARE/.test(queueBody), 'ecology queue did not drain after tick');
    await page.selectOption('#runClassSelect', 'agent-only');
    await page.click('#startRunBtn');
    await page.waitForTimeout(500);
    await page.click('#previewHouseAgentBtn');
    await page.waitForTimeout(500);
    const hintText = await page.locator('#houseAgentHint').innerText();
    assert(/House Agent/.test(hintText), 'house agent hint block did not render');
    await page.selectOption('#baselinePolicySelect', 'arena-spam');
    await page.click('#previewBaselineBtn');
    await page.waitForTimeout(400);
    const baselineHint = await page.locator('#baselineHint').innerText();
    assert(/arena-spam|ENTER_ARENA|REST/i.test(baselineHint), 'baseline preview did not render');
    await page.click('#runBaselineTickBtn');
    await page.waitForTimeout(800);
    await page.click('#tickOnceBtn');
    await page.waitForTimeout(1200);
    const body = await page.locator('body').innerText();
    assert(/The Arena/.test(body), 'ecology page did not render arena surface');
    const welfare = await page.locator('#scoreWelfare').innerText();
    const combat = await page.locator('#scoreCombat').innerText();
    const expedition = await page.locator('#scoreExpedition').innerText();
    assert(/\d+/.test(welfare) && /\d+/.test(combat) && /\d+/.test(expedition), 'ecology scores did not render');
    const replay = await page.locator('#replayArea').innerText();
    const tickReport = await page.locator('#tickReportArea').innerText();
    const inspect = await page.locator('#inspectArea').innerText();
    const leaderboards = await page.locator('#leaderboardArea').innerText();
    assert(/CARE|REST|ENTER_ARENA|HOLD|tick/i.test(tickReport), 'ecology tick report did not render passive execution');
    assert(/ENTER_ARENA|CARE|action_applied/i.test(replay), 'ecology replay did not log ecological actions');
    assert(/Run status|Latest transition|Score breakdown|Benchmark position/i.test(inspect), 'ecology inspect panel did not render');
    assert(/WELFARE|COMBAT|EXPEDITION|warnings/i.test(leaderboards), 'ecology leaderboards did not render');
    await context.close();
    return {
      snippet: body.slice(0, 300),
      replay: replay.slice(0, 240),
      tickReport: tickReport.slice(0, 240),
      inspect: inspect.slice(0, 240),
      leaderboards: leaderboards.slice(0, 240),
      scores: { welfare, combat, expedition },
      pageErrors,
      consoleErrors
    };
  }));

  results.push(await scenario('profile', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/profile', { waitUntil: 'domcontentloaded' });
    const body = await page.locator('body').innerText();
    assert(/CLASSIFIED/.test(body), 'profile page did not render dossier');
    await context.close();
    return { snippet: body.slice(0, 220), pageErrors, consoleErrors };
  }));

  results.push(await scenario('menagerie', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/menagerie', { waitUntil: 'domcontentloaded' });
    await page.click('.tab-btn[data-tab="bonds"]');
    const body = await page.locator('body').innerText();
    assert(/SPIRIT BOND BUFFS/.test(body), 'menagerie bond tab did not render');
    await context.close();
    return { snippet: body.slice(0, 260), pageErrors, consoleErrors };
  }));

  results.push(await scenario('breeding', async () => {
    const local = standardStorage(now);
    local.moreau_eggs = JSON.stringify([]);
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, local);
    await page.goto(baseUrl + '/island/breeding', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#mainContent', { state: 'visible' });
    await page.waitForFunction(() => document.querySelectorAll('#parentGrid .select-card').length > 0);
    const pickedParent = await clickFirstEnabled(page.locator('#parentGrid .select-card'));
    assert(pickedParent, 'breeding parent grid had no enabled cards');
    await page.waitForFunction(() => document.querySelectorAll('#donorGrid .select-card').length > 0);
    const pickedDonor = await clickFirstEnabled(page.locator('#donorGrid .select-card'));
    assert(pickedDonor, 'breeding donor grid had no selectable cards');
    const disabled = await page.locator('#beginBreedBtn').isDisabled();
    assert(disabled === false, 'breeding button stayed disabled after valid selections');
    await context.close();
    return { beginEnabled: true, pageErrors, consoleErrors };
  }));

  results.push(await scenario('genesis_partial_state', async () => {
    const local = standardStorage(now);
    local.moreau_genesis = JSON.stringify({ marks: 1, allTimeDeaths: 4, legacy: [] });
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, local);
    await page.goto(baseUrl + '/island/genesis', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.genesis-tab');
    const body = await page.locator('body').innerText();
    assert(/GENESIS PROTOCOL/.test(body), 'genesis page did not render');
    await context.close();
    return { snippet: body.slice(0, 240), pageErrors, consoleErrors };
  }));

  results.push(await scenario('succession', async () => {
    const { context, page, pageErrors, consoleErrors } = await makePage(browser, standardStorage(now));
    await page.goto(baseUrl + '/island/succession', { waitUntil: 'domcontentloaded' });
    const body = await page.locator('body').innerText();
    assert(/THE SUCCESSION/.test(body), 'succession page did not render');
    await context.close();
    return { snippet: body.slice(0, 220), pageErrors, consoleErrors };
  }));

  await browser.close();
  return results;
}

function summarize(results) {
  const failures = [];
  for (const result of results) {
    if (!result.ok) {
      failures.push({ name: result.name, error: result.error });
      continue;
    }
    if ((result.pageErrors || []).length > 0) {
      failures.push({ name: result.name, error: `pageErrors: ${result.pageErrors.join(' | ')}` });
    }
    if ((result.consoleErrors || []).length > 0) {
      failures.push({ name: result.name, error: `consoleErrors: ${result.consoleErrors.join(' | ')}` });
    }
  }
  return failures;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const results = await runSuite(args.baseUrl, args.headless);
  const payload = JSON.stringify(results, null, 2);
  if (args.output) {
    fs.mkdirSync(path.dirname(args.output), { recursive: true });
    fs.writeFileSync(args.output, payload, 'utf8');
  }
  console.log(payload);
  const failures = summarize(results);
  if (failures.length > 0) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
