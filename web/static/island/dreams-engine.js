// ══════════════════════════════════════════════════════════════
//  Dreams Engine — Echoes of the Island
//  Shared across Island pages for dream generation & toasts
// ══════════════════════════════════════════════════════════════

var DREAM_LIBRARY = {

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  1. ARRIVAL — pet created
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    arrival: {
        opening: "The fog parts. You're on black sand, the roar of invisible waves behind you. The Island.",
        revelations: {
            fox:       "A figure in a white coat. Dr. Moreau. 'You're quick,' he says. 'That will be useful.' He smiles. 'Or dangerous.'",
            tiger:     "The jungle vanishes. You're on an arena floor, alone. 'No past here,' echoes Dr. Moreau. 'Only what you become.'",
            bear:      "A library materializes. Books without titles. 'Every creature here is a story,' says Dr. Moreau at a lectern.",
            wolf:      "Moonlight. A forest. Dr. Moreau by a fire: 'The moon brought you here. Not chance. Fate.'",
            scorpion:  "Sand shifts beneath you. Dr. Moreau kneels: 'You were made for poison and patience. The arena needs both.'",
            boar:      "CRASH. You're through a wall. Dr. Moreau, dusting off: 'Impressive entrance. Channel that.'",
            monkey:    "Everything's upside down. Or you are. Dr. Moreau laughs: 'Chaos is just order with a sense of humor.'",
            vulture:   "High above. The Island is small from here. Dr. Moreau's voice: 'You see what others can't. Use it.'",
            rhino:     "The ground shakes. YOU did that. Dr. Moreau steps back: 'Raw power. Let's refine it.'",
            viper:     "Silence. Then a whisper. Dr. Moreau: 'The quiet ones are the most dangerous. I'm counting on that.'",
            eagle:     "Wind. Nothing but wind. Then Dr. Moreau: 'Freedom is a weapon. Most forget that.'",
            buffalo:   "Stillness. A long pause. Dr. Moreau: 'Patience and endurance. The arena breaks the impatient.'",
            panther:   "Shadow. You ARE shadow. Dr. Moreau: 'I almost didn't see you. That's the point.'",
            porcupine: "Something pricks. Your own quills. Dr. Moreau: 'Defense is its own form of attack. Remember that.'",
            'default': "A figure in white approaches. Dr. Moreau. 'Welcome,' he says. 'The Island has been waiting for you.'"
        },
        signatures: {
            fox:       "'I don't trust the smile. But I trust my speed.'",
            tiger:     "'No past. Good. I'll make my own.'",
            bear:      "'Stories... I want to read them all. After I win.'",
            wolf:      "'Fate. I can work with fate.'",
            scorpion:  "'Patience. Yes. I have plenty of that.'",
            boar:      "'CHANNEL it? I haven't even started.'",
            monkey:    "'He gets it. This is going to be FUN.'",
            vulture:   "'I see everything. Even what he's hiding.'",
            rhino:     "'Refine? Fine. But the shaking stays.'",
            viper:     "'...noted.'",
            eagle:     "'Freedom. Weapon. Same thing, really.'",
            buffalo:   "'I can wait. I can wait forever.'",
            panther:   "'...'",
            porcupine: "'Touch me. I dare you.'",
            'default': "'The Island. I'm ready.'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  2. EVOLUTION — level 3, 6, 9
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    evolution: {
        opening: "You're running through the Lab. The walls bleed. Your legs are stronger. Everything is sharper.",
        revelations: {
            '3': "The serum burns through your veins. Your muscles tighten, your senses expand. Level 3. Dr. Moreau watches from behind the glass: 'Good. The first threshold. Most don't make it this far.' You feel your old limits dissolve like smoke.",
            '6': "The second transformation is harder. Your bones ache, reshape, settle into something new. Level 6. Dr. Moreau's notes flutter to the floor as you pass: 'Subject exceeds projections. Recommend advanced mutation protocols.' The Lab doors open wider.",
            '9': "You no longer recognize what you were. Level 9. The arena trembles when you walk. Dr. Moreau sets down his pen: 'There's only one threshold left. Beyond it... I honestly don't know what happens.' For the first time, he looks afraid.",
            'default': "Something is changing. Your body, your instincts, your understanding of pain. Dr. Moreau nods slowly: 'Growth. Real growth. Not everyone survives it.'"
        },
        signatures: {
            '3': "'I can feel the difference. Everything is... louder.'",
            '6': "'The lab doors opened wider. What else is in there?'",
            '9': "'He looked afraid. Good.'",
            'default': "'Stronger. But at what cost?'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  3. PROPHECY — before lab roll
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    prophecy: {
        opening: "The Forbidden Lab. But wrong. The vials are breathing.",
        revelations: {
            '1': "Dr. Moreau's voice, but his lips aren't moving: 'Every mutation is a door. Some doors lock behind you. Some doors have no floor.' The vials pulse faster. One of them has your name on it.",
            '2': "The walls shift. Dr. Moreau is younger here, eyes bright with something terrible: 'I built this place to push boundaries. But boundaries push back.' He holds up a vial of something dark. 'This one changes everything. Or ends it.'",
            '3': "You're in the deepest part of the Lab. No lights. Just the glow of the vials. Dr. Moreau's whisper: 'I've seen what Tier 3 does. The survivors... they're not the same creature anymore. Neither are the failures. Choose carefully.'",
            'default': "Dr. Moreau appears between the shelves: 'The Lab gives and the Lab takes. What it takes, it never returns.'"
        },
        signatures: {
            confident: "'A door with no floor? I'll build wings on the way down.'",
            cautious:  "'Maybe I should think about this. ...No. Let's go.'",
            berserker: "'Doors? Floors? I'm going THROUGH the wall.'",
            'default': "'The vials are breathing. That can't be normal.'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  4. TRAUMA — comeback win
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    trauma: {
        opening: "You're drowning. The opponent is still striking. Your HP flickers in the single digits.",
        revelations: {
            'default': "Something snaps. Not breaks \u2014 unlocks. Your body moves on its own, faster than thought, harder than instinct. The opponent falls. You won. You're standing in the arena, breathing, alive. But the echo of almost-dying lingers in your muscles like a second heartbeat."
        },
        signatures: {
            fox:       "'I won. So why are my paws still shaking?'",
            tiger:     "'Victory. It tastes different when you almost lose everything.'",
            bear:      "'That wasn't strategy. That was survival. Pure, ugly survival.'",
            wolf:      "'The pack would be proud. But the pack wasn't here. I was alone.'",
            scorpion:  "'I felt my venom run dry. Then somehow... more came.'",
            boar:      "'I don't remember the last ten seconds. Just the impact. Then silence.'",
            monkey:    "'That wasn't funny. None of that was funny. ...okay, the look on their face at the end was a little funny.'",
            vulture:   "'I saw my own death from above. Then I chose a different ending.'",
            rhino:     "'I couldn't feel my legs. Then I couldn't feel anything. Then I won.'",
            viper:     "'One more second and it would have been me on the ground. One second.'",
            eagle:     "'I fell. Eagles aren't supposed to fall. But I got back up.'",
            buffalo:   "'They hit me with everything. Everything. It wasn't enough.'",
            panther:   "'I vanished into the pain. Came out the other side as something sharper.'",
            porcupine: "'Every quill fired. Every single one. And it still almost wasn't enough.'",
            'default': "'I won. But something in me remembers losing.'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  5. CORRUPTION — Tier 3 mutation
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    corruption: {
        opening: "Dr. Moreau's lab. You're on the table. The mutation glows \u2014 not like light, like hunger.",
        revelations: {
            'default': "The Tier 3 serum enters your bloodstream and the world turns inside out. Colors you've never seen. Sounds from frequencies that shouldn't exist. Dr. Moreau watches, pen frozen mid-note. 'This cost something,' he says quietly. 'They always do.' When it's over, you're different. The mirror shows your face, but the eyes belong to something else."
        },
        signatures: {
            'default': "'I can hear the mutation's heartbeat. It sounds like mine. Or maybe mine sounds like it now.'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  6. DEATH — pet dies
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    death: {
        opening: "The Lab fades. The Island fades. A quiet place. No pain here. No arena. Just... quiet.",
        revelations: {
            'default': "Dr. Moreau is here, but different. No coat. No clipboard. Just a man, tired, sitting in a chair. 'I'm sorry,' he says. Not a scientist now \u2014 just someone who lost something. 'You were brave. All of you are brave. That's the cruelest part.' Behind him, other shapes move in the quiet. Other pets. Other experiments. They nod at you. They know."
        },
        signatures: {
            fox:       "'Tell them I was faster than they thought. Tell them I almost made it.'",
            tiger:     "'No regrets. I fought like a tiger. I died like one too.'",
            bear:      "'The stories... I never finished reading them. Maybe the next one will.'",
            wolf:      "'The moon is different here. Quieter. I think I'll stay.'",
            scorpion:  "'My venom is fading. But the sting... the sting lasts forever.'",
            boar:      "'I went out swinging. That's all I ever wanted.'",
            monkey:    "'Last joke: I finally found a game I can't win. ...that's not funny, is it.'",
            vulture:   "'From up here, the Island looks so small. All of it. So small.'",
            rhino:     "'The ground doesn't shake anymore. I think it misses me.'",
            viper:     "'Silence. At last, real silence. It's... not so bad.'",
            eagle:     "'No more wind. No more sky. But I remember what freedom felt like.'",
            buffalo:   "'I stood my ground until the ground gave out. That's enough.'",
            panther:   "'I return to the shadow. Where I started. Where I belong.'",
            porcupine: "'My quills are gone. For the first time, nothing hurts. Nothing at all.'",
            'default': "'It was a good fight. All of them were.'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  7. TRANSCENDENCE — Apex Form
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    transcendence: {
        opening: "All mutations spiral like a constellation. They're singing. Not a melody \u2014 a frequency. YOUR frequency.",
        revelations: {
            'default': "The Lab dissolves. The arena dissolves. You're standing in the center of everything and nothing. Dr. Moreau is there, but he's far below now, looking up. 'You found the combination,' he whispers. 'Not by reading the formula. Not by following instructions. By becoming.' The mutations stop spinning. They're part of you now. They always were."
        },
        signatures: {
            'default': "'I am [APEX_NAME]. I was always [APEX_NAME]. The mutations didn't change me. They revealed me.'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  8. SPIRIT_IMMORTALIZED — Menagerie immortalization
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    spirit_immortalized: {
        opening: "The Menagerie glows. A pedestal rises from the ground. Something eternal is being carved.",
        revelations: {
            fox:       "Your spirit flickers into the stone, grinning. The Menagerie will remember that smile forever.",
            tiger:     "Stripes etch themselves into marble. The arena's fiercest, preserved in eternal roar.",
            bear:      "A gentle giant, frozen mid-stride. The books in the Menagerie rustle in recognition.",
            wolf:      "Moonlight catches the statue's eyes. The pack howls somewhere beyond the walls.",
            scorpion:  "The tail curls upward in stone, venom glistening even in death. A warning for eternity.",
            boar:      "The charge captured forever. Visitors feel the ground tremble when they stand too close.",
            monkey:    "The statue is smiling. No — laughing. Even immortality can't make you serious.",
            vulture:   "Wings spread wide in obsidian. From this height, even time looks small.",
            rhino:     "The pedestal cracked when they placed you. Even stone respects your weight.",
            viper:     "Coiled in jade, silent and patient. Visitors whisper that the eyes follow them.",
            eagle:     "Carved from wind and memory. The Menagerie's highest perch, claimed forever.",
            buffalo:   "Steady and immovable. The Menagerie's foundation stone, they'll call you.",
            panther:   "A shadow pressed into crystal. You're there if you look. Most don't look.",
            porcupine: "Every quill rendered in silver. Touch the statue. We dare you.",
            'default': "Your form is captured in the Menagerie. Not as you were — as you truly are."
        },
        signatures: {
            fox:       "'Immortal. I always knew I was too good to forget.'",
            tiger:     "'Let them see what the arena made. Let them remember.'",
            bear:      "'A story that never ends. I like that.'",
            wolf:      "'The moon will always find me here.'",
            scorpion:  "'Even in stone, I sting.'",
            boar:      "'FOREVER. That's how long I'll charge.'",
            monkey:    "'A statue of ME? This is the best joke yet.'",
            vulture:   "'From up here, I can see everything. Even tomorrow.'",
            rhino:     "'Unbreakable in life. Unbreakable in stone.'",
            viper:     "'Sssilence. For eternity. Perfect.'",
            eagle:     "'Freedom, carved in permanence. Ironic. Beautiful.'",
            buffalo:   "'I'll stand here. I'll stand here forever. I don't mind.'",
            panther:   "'...' (The plaque reads: HERE. ALWAYS.)",
            porcupine: "'Touch it. Go on. Some lessons are eternal.'",
            'default': "'This is what forever feels like. It feels like home.'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  9. SPIRIT_BONDED — Spirit bond events
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    spirit_bonded: {
        opening: "A presence brushes against yours. Not physical — deeper. A spirit reaches out.",
        revelations: {
            fox:       "The spirit mirrors your cunning. Two foxes, circling, then merging into one shared instinct.",
            tiger:     "Raw power meets raw power. The spirit bond crackles like lightning between two storms.",
            bear:      "The spirit settles beside you like a second heartbeat. Warm. Patient. Knowing.",
            wolf:      "The spirit howls in a frequency only you can hear. Your bond is the pack itself.",
            scorpion:  "The spirit coils around your venom gland. Your poison deepens, your patience sharpens.",
            boar:      "Impact. The spirit hits you like a wall, then flows through you. You are harder now.",
            monkey:    "The spirit laughs with you. Or at you. Hard to tell. The bond is chaos, and it's perfect.",
            vulture:   "The spirit lifts you higher. From this vantage, you see patterns no one else can read.",
            rhino:     "The ground shakes as the spirit merges. Two unstoppable forces, now one.",
            viper:     "The spirit slides along your scales. Silent. Lethal. The bond needs no words.",
            eagle:     "Wind carries the spirit into you. Your wings stretch wider, your vision sharper.",
            buffalo:   "The spirit anchors into your stance. Roots grow from your hooves. Immovable.",
            panther:   "Shadow meets shadow. The bond is invisible. That's the point.",
            porcupine: "The spirit wraps around your quills. Each one hums with borrowed resonance.",
            'default': "The spirit bond forms — a thread of light connecting you to something ancient and alive."
        },
        signatures: {
            fox:       "'Two minds. One hunt. I like these odds.'",
            tiger:     "'The spirit knows my strength. It fears nothing. Neither do I.'",
            bear:      "'A friend. In this place, that means everything.'",
            wolf:      "'The pack grows. Even beyond death.'",
            scorpion:  "'Our patience is doubled now. Pity them.'",
            boar:      "'Harder. Faster. More. MORE.'",
            monkey:    "'It gets my jokes. FINALLY.'",
            vulture:   "'I see further than ever. The horizon bows.'",
            rhino:     "'Two forces. One direction. Forward.'",
            viper:     "'The silence between us says everything.'",
            eagle:     "'Higher. Always higher.'",
            buffalo:   "'Rooted. Together. Unshakable.'",
            panther:   "'We vanish together. Twice the shadow.'",
            porcupine: "'Touch us. I double-dare you.'",
            'default': "'Connected. Not alone anymore. That changes things.'"
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    //  10. DISCOVERY — Artifact/shrine discoveries
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    discovery: {
        opening: "Something gleams in the undergrowth. The Island has revealed one of its secrets.",
        revelations: {
            fox:       "Your nose found it first. Buried under roots, wrapped in old cloth. An artifact from before the arena.",
            tiger:     "You tore through the brush and there it was — glowing, ancient, waiting for something strong enough to claim it.",
            bear:      "You were reading the moss patterns when you noticed it. Hidden in plain sight. A relic with a story.",
            wolf:      "The moon pointed you here. A clearing, a shrine, a gift the Island saved for the worthy.",
            scorpion:  "You dug. Patiently, carefully. Beneath the sand, a prize the impatient would never find.",
            boar:      "You crashed through the wall and it fell into your lap. Sometimes brute force IS the answer.",
            monkey:    "You found it hanging from a vine. Or it found you. Either way — finders keepers.",
            vulture:   "You spotted it from above. A glint between the trees. Down you swooped. Yours now.",
            rhino:     "The ground cracked open and there it was. The Island knows you don't do subtle.",
            viper:     "You sensed it — a vibration in the earth. You followed it to a hidden shrine.",
            eagle:     "Wind carried a scent. You followed it to a cliff ledge. An artifact, sun-bleached and powerful.",
            buffalo:   "You stood in one place long enough for the Island to trust you. It opened. You received.",
            panther:   "In the deepest shadow, something shimmered. Only you could have found it. Only shadow sees shadow.",
            porcupine: "Your quills tingled near the old tree. You investigated. The shrine was inside the trunk.",
            'default': "The Island reveals its secrets to those who explore. Today, it chose you."
        },
        signatures: {
            fox:       "'Hidden things find me. It's a gift.'",
            tiger:     "'The Island gives its treasures to the strong. Naturally.'",
            bear:      "'Every artifact has a story. I want to know all of them.'",
            wolf:      "'The moon guides. I follow. It never leads me wrong.'",
            scorpion:  "'Patience pays. It always pays.'",
            boar:      "'I didn't find it. I MADE the Island give it up.'",
            monkey:    "'Ooh, shiny. MINE.'",
            vulture:   "'Nothing escapes my eyes. Nothing.'",
            rhino:     "'The ground opens for me. Smart ground.'",
            viper:     "'I felt it before I saw it. The vibration never lies.'",
            eagle:     "'From above, everything is visible. Even secrets.'",
            buffalo:   "'Patience. The Island respects patience.'",
            panther:   "'Shadows hide things. Shadows also reveal them. To me.'",
            porcupine: "'My quills sensed it. They sense everything.'",
            'default': "'Found something. The Island has more secrets. I'll find those too.'"
        }
    }
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  HAUNTING VOICES — Confession Echoes
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

var HAUNTING_VOICES = {
    fox: "Three steps ahead... even in death. Did you think I'd just disappear?",
    bear: "I didn't want to fight. You knew that. And still you let them take me.",
    tiger: "Efficient. That's what you called it when you chose.",
    wolf: "The pack remembers. Every howl carries a name you tried to forget.",
    boar: "I charged into everything. Even the end. You just watched.",
    monkey: "I used to make you laugh. Do you remember laughing?",
    buffalo: "I stood my ground. Every time. Who stood for me?",
    porcupine: "I kept everyone at a distance. Except you. That was my mistake.",
    scorpion: "Poison runs both ways. You'll feel this sting for a while.",
    vulture: "I waited patiently for scraps of your attention. Fitting end, wasn't it?",
    rhino: "Unstoppable, they said. Until someone stops caring.",
    viper: "Sssilence now. But I still whisper in the spaces between your thoughts.",
    eagle: "I saw everything from above. Including the moment you gave up on me.",
    panther: "In the dark, we're the same. You just haven't realized it yet."
};

var CONVERGENCE_TEXT = "We are still here. All of us. Fox, Bear, Tiger \u2014 names you gave, names you took away. We don't blame you. We don't forgive you either. We simply... remain. In the static between your thoughts. In the pause before you choose. We are the weight you carry. And we are waiting.";

// ── Check for confession echoes ──

function shouldGenerateHaunting() {
    try {
        var confessions = JSON.parse(localStorage.getItem('moreau_confessions') || '[]');
        if (confessions.length === 0) return null;

        // 40% chance of haunting dream after any confession exists
        if (Math.random() > 0.4) return null;

        // Pick a random dead pet from confessions
        var deadPets = [];
        var allPets = JSON.parse(localStorage.getItem('moreau_pets') || '[]');
        for (var i = 0; i < allPets.length; i++) {
            if (allPets[i].deceased) deadPets.push(allPets[i]);
        }
        if (deadPets.length === 0) return null;

        var ghost = deadPets[Math.floor(Math.random() * deadPets.length)];
        return ghost;
    } catch(e) { return null; }
}

// ── Special dream when resurrection token threshold reached ──

function checkConvergence() {
    try {
        var confessions = JSON.parse(localStorage.getItem('moreau_confessions') || '[]');
        var convergenceShown = localStorage.getItem('moreau_dream_convergence');
        if (confessions.length >= 20 && !convergenceShown) {
            localStorage.setItem('moreau_dream_convergence', 'true');
            return true;
        }
    } catch(e) {}
    return false;
}

// ── Generate a dream and store it ──

function generateDream(type, pet, extra) {
    extra = extra || {};
    var dreams = JSON.parse(localStorage.getItem('moreau_dreams') || '{"dreams":[],"unread_count":0}');
    var animal = (pet.animal || '').toLowerCase();

    // ── Check for CONVERGENCE first (20+ confessions, one-time) ──
    if (checkConvergence()) {
        var deadPetNames = [];
        try {
            var allPetsConv = JSON.parse(localStorage.getItem('moreau_pets') || '[]');
            for (var ci = 0; ci < allPetsConv.length; ci++) {
                if (allPetsConv[ci].deceased) deadPetNames.push(allPetsConv[ci].name);
            }
        } catch(e) {}

        var convergenceDream = {
            id: 'dream_convergence_' + Date.now(),
            pet_name: 'All of them',
            pet_animal: '',
            type: 'convergence',
            text: CONVERGENCE_TEXT,
            opening: CONVERGENCE_TEXT,
            revelation: '',
            signature: '',
            petNames: deadPetNames,
            timestamp: new Date().toISOString(),
            read: false,
            favorite: false
        };

        dreams.dreams.unshift(convergenceDream);
        dreams.unread_count = dreams.dreams.filter(function(d) { return !d.read; }).length;
        if (dreams.dreams.length > 50) dreams.dreams = dreams.dreams.slice(0, 50);
        localStorage.setItem('moreau_dreams', JSON.stringify(dreams));
        showDreamToast(convergenceDream);
        // Still generate the original dream below
    }

    // ── Check for HAUNTING (40% chance if confessions exist) ──
    var ghost = shouldGenerateHaunting();
    if (ghost) {
        var ghostAnimal = (ghost.animal || '').toLowerCase();
        var hauntingText = HAUNTING_VOICES[ghostAnimal] || HAUNTING_VOICES['fox'];

        var hauntingDream = {
            id: 'dream_haunting_' + Date.now(),
            pet_name: ghost.name || 'Unknown',
            pet_animal: ghostAnimal,
            type: 'haunting',
            animal: ghostAnimal,
            text: hauntingText,
            opening: hauntingText,
            revelation: '',
            signature: '',
            ghostOf: ghost.name,
            timestamp: new Date().toISOString(),
            read: false,
            favorite: false
        };

        dreams.dreams.unshift(hauntingDream);
        dreams.unread_count = dreams.dreams.filter(function(d) { return !d.read; }).length;
        if (dreams.dreams.length > 50) dreams.dreams = dreams.dreams.slice(0, 50);
        localStorage.setItem('moreau_dreams', JSON.stringify(dreams));
        showDreamToast(hauntingDream);
        // Still generate the original dream below
    }

    // ── Normal dream generation ──
    var text = DREAM_LIBRARY[type];
    if (!text) return;

    // Determine revelation key
    var revKey = animal;
    if (type === 'evolution') {
        revKey = String(extra.level || pet.level || '3');
    } else if (type === 'prophecy') {
        var variants = ['1', '2', '3'];
        revKey = variants[Math.floor(Math.random() * variants.length)];
    }

    // Determine signature key
    var sigKey = animal;
    if (type === 'evolution') {
        sigKey = String(extra.level || pet.level || '3');
    } else if (type === 'prophecy') {
        var personalities = ['confident', 'cautious', 'berserker'];
        // Pick based on pet stats
        var bs = pet.base_stats || {};
        if ((bs.atk || 0) >= 7) sigKey = 'berserker';
        else if ((bs.wil || 0) >= 6) sigKey = 'cautious';
        else sigKey = 'confident';
    }

    var revelation = (text.revelations && (text.revelations[revKey] || text.revelations['default'])) || '';
    var signature = (text.signatures && (text.signatures[sigKey] || text.signatures['default'])) || '';

    var dream = {
        id: 'dream_' + type + '_' + Date.now(),
        pet_name: pet.name || 'Unknown',
        pet_animal: animal,
        type: type,
        opening: text.opening || '',
        revelation: revelation,
        signature: signature,
        timestamp: new Date().toISOString(),
        read: false,
        favorite: false
    };

    // For transcendence, substitute apex name
    if (type === 'transcendence' && extra.apex_name) {
        dream.signature = dream.signature.replace(/\[APEX_NAME\]/g, extra.apex_name);
    }

    dreams.dreams.unshift(dream);
    dreams.unread_count = dreams.dreams.filter(function(d) { return !d.read; }).length;
    if (dreams.dreams.length > 50) dreams.dreams = dreams.dreams.slice(0, 50);
    localStorage.setItem('moreau_dreams', JSON.stringify(dreams));

    // Show toast
    showDreamToast(dream);
}

// ── Dream toast notification ──

function showDreamToast(dream) {
    var typeColors = {
        arrival: '#4ecca3',
        evolution: '#4ecca3',
        prophecy: '#457b9d',
        trauma: '#e63946',
        corruption: '#e63946',
        death: '#6a5a5a',
        transcendence: '#d4a017',
        spirit_immortalized: '#d4a017',
        spirit_bonded: '#9b59b6',
        discovery: '#4ecca3',
        haunting: '#e63946',
        convergence: '#d4a017'
    };
    var color = typeColors[dream.type] || '#9b59b6';

    var toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;top:1.5rem;left:50%;transform:translateX(-50%);z-index:9999;' +
        'background:#1a1010;border:2px solid ' + color + ';border-radius:8px;padding:0.75rem 1.5rem;' +
        'display:flex;align-items:center;gap:0.75rem;box-shadow:0 4px 24px ' + color + '40;' +
        'animation:dreamToastIn 0.4s ease-out;font-family:Inter,system-ui,sans-serif;max-width:90vw;cursor:pointer;';
    var toastIcon = '&#10022;';
    var toastLabel = 'New Dream';
    if (dream.type === 'haunting') { toastIcon = '&#128123;'; toastLabel = 'Haunting'; }
    else if (dream.type === 'convergence') { toastIcon = '&#10022;'; toastLabel = 'Convergence'; }

    toast.innerHTML =
        '<span style="font-size:1.3rem;">' + toastIcon + '</span>' +
        '<div>' +
            '<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;color:' + color + ';font-weight:700;">' + toastLabel + '</div>' +
            '<div style="font-size:0.85rem;font-weight:600;color:#f1faee;">' + (dream.pet_name || '') + ' \u2014 ' + (dream.type || 'dream') + '</div>' +
        '</div>';

    toast.onclick = function() {
        window.location.href = '/island/dreams';
    };

    // Add animation keyframes if not present
    if (!document.getElementById('dream-toast-keyframes')) {
        var style = document.createElement('style');
        style.id = 'dream-toast-keyframes';
        style.textContent =
            '@keyframes dreamToastIn{from{opacity:0;transform:translateX(-50%) translateY(-20px);}to{opacity:1;transform:translateX(-50%) translateY(0);}}' +
            '@keyframes dreamToastOut{from{opacity:1;transform:translateX(-50%) translateY(0);}to{opacity:0;transform:translateX(-50%) translateY(-20px);}}';
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    setTimeout(function() {
        toast.style.animation = 'dreamToastOut 0.4s ease-in forwards';
        setTimeout(function() { toast.remove(); }, 400);
    }, 5000);
}
