// ══════════════════════════════════════════════
//  Supabase Client — shared across all /island pages
//  Include AFTER the Supabase CDN script
// ══════════════════════════════════════════════

// Config loaded from server endpoint
let SUPABASE_URL = '';
let SUPABASE_ANON_KEY = '';

let sb = null;
let currentUser = null;

async function initSupabase() {
    // Fetch config from server
    if (!SUPABASE_URL) {
        try {
            const resp = await fetch('/api/v1/island/config');
            const cfg = await resp.json();
            SUPABASE_URL = cfg.supabase_url || '';
            SUPABASE_ANON_KEY = cfg.supabase_anon_key || '';
        } catch (e) {
            console.warn('[Island] Could not fetch config:', e);
        }
    }
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
        console.warn('[Island] Supabase not configured. Running in offline/localStorage mode.');
        return null;
    }
    try {
        sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        return sb;
    } catch (e) {
        console.error('[Island] Supabase init failed:', e);
        return null;
    }
}

// ── Auth helpers ──

async function getUser() {
    if (!sb) return null;
    try {
        const { data: { user } } = await sb.auth.getUser();
        currentUser = user;
        return user;
    } catch {
        return null;
    }
}

async function signInWithGoogle() {
    if (!sb) { alert('Supabase not configured yet. Coming soon!'); return; }
    const { error } = await sb.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: window.location.origin + '/island/home' }
    });
    if (error) alert('Login failed: ' + error.message);
}

async function signInWithEmail(email, password) {
    if (!sb) { alert('Supabase not configured yet. Coming soon!'); return; }
    const { error } = await sb.auth.signInWithPassword({ email, password });
    if (error) {
        // Try sign up if login fails
        const { error: signUpError } = await sb.auth.signUp({
            email, password,
            options: { emailRedirectTo: window.location.origin + '/island/home' }
        });
        if (signUpError) alert('Auth failed: ' + signUpError.message);
        else alert('Check your email for verification link!');
        return;
    }
    window.location.href = '/island/home';
}

async function signOut() {
    if (!sb) return;
    await sb.auth.signOut();
    currentUser = null;
    window.location.href = '/island';
}

// ── Auth state listener ──

function onAuthChange(callback) {
    if (!sb) return;
    sb.auth.onAuthStateChange((event, session) => {
        currentUser = session?.user || null;
        callback(event, session, currentUser);
    });
}

// ── Pet CRUD (DB) ──

async function dbGetPets(userId) {
    if (!sb) return [];
    const { data, error } = await sb.from('pets').select('*')
        .eq('user_id', userId).order('created_at');
    if (error) { console.error('[Island] dbGetPets:', error); return []; }
    return data || [];
}

async function dbCreatePet(userId, pet) {
    if (!sb) return null;
    const { data, error } = await sb.from('pets').insert({
        user_id: userId,
        name: pet.name,
        animal: pet.animal,
        base_stats: pet.base_stats,
        level: pet.level || 1,
        xp: pet.xp || 0,
        mutations: pet.mutations || [],
        lab_mutations: pet.lab_mutations || {},
        side_effects: pet.side_effects || [],
        instability: pet.instability || 0,
        scars: pet.scars || 0,
        mercy_used: pet.mercy_used || false,
        mood: pet.mood || 'neutral',
        is_alive: true,
        fights_won: pet.fights_won || 0,
        fights_lost: pet.fights_lost || 0
    }).select().single();
    if (error) { console.error('[Island] dbCreatePet:', error); return null; }
    return data;
}

async function dbUpdatePet(petId, updates) {
    if (!sb) return null;
    const { data, error } = await sb.from('pets').update(updates)
        .eq('id', petId).select().single();
    if (error) { console.error('[Island] dbUpdatePet:', error); return null; }
    return data;
}

async function dbDeletePet(petId) {
    if (!sb) return false;
    const { error } = await sb.from('pets').delete().eq('id', petId);
    if (error) { console.error('[Island] dbDeletePet:', error); return false; }
    return true;
}

async function dbKillPet(petId) {
    return dbUpdatePet(petId, { is_alive: false, died_at: new Date().toISOString() });
}

// ── Fights ──

async function dbRecordFight(fight) {
    if (!sb) return null;
    const { data, error } = await sb.from('fights').insert(fight).select().single();
    if (error) { console.error('[Island] dbRecordFight:', error); return null; }
    return data;
}

// ── Codex ──

async function dbDiscoverMutation(userId, mutationId) {
    if (!sb) return;
    await sb.from('mutations_codex').upsert({
        user_id: userId,
        mutation_id: mutationId,
        discovered_at: new Date().toISOString()
    }, { onConflict: 'user_id,mutation_id' });
}

async function dbGetCodex(userId) {
    if (!sb) return {};
    const { data } = await sb.from('mutations_codex').select('mutation_id')
        .eq('user_id', userId);
    const codex = {};
    (data || []).forEach(r => { codex[r.mutation_id] = true; });
    return codex;
}

// ── Graveyard ──

async function dbGetGraveyard(limit) {
    if (!sb) return [];
    const { data } = await sb.from('pets').select('*, users!inner(display_name)')
        .eq('is_alive', false)
        .order('died_at', { ascending: false })
        .limit(limit || 50);
    return data || [];
}

// ── Leaderboard ──

async function dbGetLeaderboard(limit) {
    if (!sb) return [];
    const { data } = await sb.from('pets').select('*, users!inner(display_name)')
        .eq('is_alive', true)
        .order('fights_won', { ascending: false })
        .limit(limit || 50);
    return data || [];
}

// ── localStorage Migration ──

async function migrateLocalStorageToDB(userId) {
    const petsRaw = localStorage.getItem('moreau_pets');
    if (!petsRaw) return { migrated: 0 };

    let pets;
    try { pets = JSON.parse(petsRaw); } catch { return { migrated: 0 }; }
    if (!Array.isArray(pets) || pets.length === 0) return { migrated: 0 };

    let migrated = 0;
    for (const p of pets) {
        const result = await dbCreatePet(userId, {
            name: p.name,
            animal: p.animal,
            base_stats: p.base_stats || p.stats || { hp: 5, atk: 5, spd: 5, wil: 5 },
            level: p.level || 1,
            xp: p.xp || 0,
            mutations: p.mutations || [],
            lab_mutations: p.lab_mutations || {},
            side_effects: p.side_effects || [],
            instability: p.instability || 0,
            scars: p.scars || 0,
            mercy_used: p.mercy_used || false,
            mood: p.mood || 'neutral',
            fights_won: (p.fights || []).filter(f => f.result === 'win').length,
            fights_lost: (p.fights || []).filter(f => f.result === 'loss').length
        });
        if (result) migrated++;
    }

    // Migrate codex
    const codexRaw = localStorage.getItem('moreau_codex');
    if (codexRaw) {
        try {
            const codex = JSON.parse(codexRaw);
            for (const mutId of Object.keys(codex)) {
                await dbDiscoverMutation(userId, mutId);
            }
        } catch {}
    }

    // Clear localStorage after successful migration
    if (migrated > 0) {
        localStorage.removeItem('moreau_pets');
        localStorage.removeItem('moreau_active_pet');
        localStorage.removeItem('moreau_pet');
        localStorage.removeItem('moreau_codex');
        localStorage.removeItem('moreau_pit_history');
        localStorage.removeItem('moreau_ultra_rare_post');
    }

    return { migrated };
}

// ── Offline fallback (use localStorage when Supabase isn't configured) ──

function isOnlineMode() {
    return sb !== null && currentUser !== null;
}
