from itertools import zip_longest, cycle, product
inv ="""sexy
lewd
erotic
scandalous
exposing
bdsm
slutty""".split("\n")
inv2 ="""red
orange
cyan
purple
emerald""".split("\n")
inv3 ="""bikini
bra
pantie
lingerie""".split("\n")

#open("mixer.py", "a").writelines([f"{adj} {cloth}, {color}\n" for adj, color, cloth in product(inv, inv2, inv3)])
open("mixer.py", "a").write(f"{'|'.join(inv)} {'|'.join(inv2)}, {'|'.join(inv3)}\n" )
{$$sexy|lewd|erotic|scandalous|exposing|bdsm|slutty} {$$red|orange|cyan|purple|emerald}, {$$bikini|bra|pantie|lingerie}
