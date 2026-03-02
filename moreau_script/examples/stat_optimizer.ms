# Stat optimizer: maximize ATK against low-HP opponents
IF opponent.last_build.hp < 5:
  PREFER animal="BEAR", atk=MAX
ELIF opponent.last_build.atk > 12:
  PREFER animal="BUFFALO", hp=MAX
ELSE:
  PREFER animal="TIGER", atk=8, spd=6
