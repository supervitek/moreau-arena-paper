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
    }
};

// ── Generate a dream and store it ──

function generateDream(type, pet, extra) {
    extra = extra || {};
    var dreams = JSON.parse(localStorage.getItem('moreau_dreams') || '{"dreams":[],"unread_count":0}');
    var animal = (pet.animal || '').toLowerCase();
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
        var bs = pet.base_stats || pet.stats || {};
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
        transcendence: '#d4a017'
    };
    var color = typeColors[dream.type] || '#9b59b6';

    var toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;top:1.5rem;left:50%;transform:translateX(-50%);z-index:9999;' +
        'background:#1a1010;border:2px solid ' + color + ';border-radius:8px;padding:0.75rem 1.5rem;' +
        'display:flex;align-items:center;gap:0.75rem;box-shadow:0 4px 24px ' + color + '40;' +
        'animation:dreamToastIn 0.4s ease-out;font-family:Inter,system-ui,sans-serif;max-width:90vw;cursor:pointer;';
    toast.innerHTML =
        '<span style="font-size:1.3rem;">&#10022;</span>' +
        '<div>' +
            '<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;color:' + color + ';font-weight:700;">New Dream</div>' +
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
