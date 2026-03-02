# Counter-pick strategy
IF opponent.animal == "BEAR":
  PREFER animal="BUFFALO", hp=8, atk=6, spd=4, wil=2
ELIF opponent.animal == "TIGER":
  PREFER animal="BEAR", hp=4, atk=13, spd=2, wil=1
ELIF opponent.animal == "BOAR":
  PREFER animal="BEAR", hp=3, atk=14, spd=2, wil=1
ELSE:
  PREFER animal="BOAR", hp=8, atk=8, spd=3, wil=1
