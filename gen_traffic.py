import osmium, csv

PEAK = {  # ضریب ساعت ۷-۸ نسبت به free-flow
    "motorway": 0.50, "motorway_link": 0.50,
    "trunk": 0.50, "trunk_link": 0.55,
    "primary": 0.55, "primary_link": 0.60,
    "secondary": 0.65, "tertiary": 0.75,
    "residential": 0.85, "unclassified": 0.85,
    "living_street": 0.95, "service": 0.95,
}
FREEFLOW = {  # هم‌تراز با car.lua
    "motorway": 90, "motorway_link": 45, "trunk": 85, "trunk_link": 40,
    "primary": 65, "primary_link": 30, "secondary": 55, "tertiary": 40,
    "residential": 25, "unclassified": 25, "living_street": 10, "service": 15,
}

class H(osmium.SimpleHandler):
    def __init__(self, w): super().__init__(); self.w = w
    def way(self, way):
        hw = way.tags.get("highway")
        if hw not in PEAK: return
        base = way.tags.get("maxspeed")
        try: base = int(str(base).split()[0])
        except: base = FREEFLOW[hw]
        spd = max(5, round(base * PEAK[hw]))
        oneway = way.tags.get("oneway") in ("yes", "true", "1")
        nodes = [n.ref for n in way.nodes]
        for a, b in zip(nodes, nodes[1:]):
            self.w.writerow([a, b, spd, spd])
            if not oneway:
                self.w.writerow([b, a, spd, spd])

with open("traffic_07_08.csv", "w", newline="") as f:
    H(csv.writer(f)).apply_file("iran-latest.osm.pbf")
