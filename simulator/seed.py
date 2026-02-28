"""Deterministic seed derivation for Moreau Arena.

All random events must use these functions. Never use random.random() directly.
Seed chain: match_seed -> tick_seed -> hit_seed -> seeded_random()
"""

import hashlib
import struct


def derive_tick_seed(match_seed: int, tick_index: int) -> int:
    """Derive a tick-specific seed from match seed and tick index."""
    data = struct.pack(">QI", match_seed, tick_index)
    h = hashlib.sha256(data).digest()
    return struct.unpack(">I", h[:4])[0]


def derive_hit_seed(match_seed: int, tick_index: int, attack_index: int) -> int:
    """Derive a hit-specific seed from match seed, tick, and attack index."""
    data = struct.pack(">QII", match_seed, tick_index, attack_index)
    h = hashlib.sha256(data).digest()
    return struct.unpack(">I", h[:4])[0]


def seeded_random(seed: int, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Generate a deterministic random float in [min_val, max_val] from a seed.

    Uses seed to produce a uniform float, then scales to range.
    """
    # Mask to uint32 to handle arithmetic overflow from callers
    seed = seed & 0xFFFFFFFF
    data = struct.pack(">I", seed)
    h = hashlib.sha256(data).digest()
    # Convert first 8 bytes to uint64, normalize to [0, 1)
    raw = struct.unpack(">Q", h[:8])[0]
    normalized = raw / (2**64)
    return min_val + normalized * (max_val - min_val)


def seeded_bool(seed: int, probability: float) -> bool:
    """Return True with given probability, deterministically from seed."""
    return seeded_random(seed) < probability


def derive_proc_seed(
    match_seed: int,
    tick_index: int,
    creature_index: int,
    ability_index: int,
) -> int:
    """Derive a proc-specific seed for ability proc rolls.

    Uses SHA-256 with packed (match_seed:u64, tick_index:u32,
    creature_index:u8, ability_index:u8).
    """
    data = struct.pack(">QIBB", match_seed, tick_index, creature_index, ability_index)
    h = hashlib.sha256(data).digest()
    return struct.unpack(">I", h[:4])[0]
