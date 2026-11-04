import argparse
import csv

import osmium

FREEFLOW = {  # هم‌تراز با car.lua
    "motorway": 90, "motorway_link": 45, "trunk": 85, "trunk_link": 40,
    "primary": 65, "primary_link": 30, "secondary": 55, "tertiary": 40,
    "residential": 25, "unclassified": 25, "living_street": 10, "service": 15,
}

# ضرایب هر باکت نسبت به free-flow
PEAK = {
    "motorway": 0.50, "motorway_link": 0.50,
    "trunk": 0.50, "trunk_link": 0.55,
    "primary": 0.55, "primary_link": 0.60,
    "secondary": 0.65, "tertiary": 0.75,
    "residential": 0.85, "unclassified": 0.85,
    "living_street": 0.95, "service": 0.95,
}
OFFPEAK = {k: min(1.0, v + 0.25) for k, v in PEAK.items()}
NIGHT = {k: 1.0 for k in PEAK}


def factors_for_hour(hour: int) -> dict:
    """باکت زمانی را از ساعت روز انتخاب می‌کند."""
    if 7 <= hour < 10 or 17 <= hour < 20:
        return PEAK
    if 22 <= hour or hour < 6:
        return NIGHT
    return OFFPEAK


class TrafficHandler(osmium.SimpleHandler):
    def __init__(self, writer, factors):
        super().__init__()
        self.writer = writer
        self.factors = factors
        self.rows = 0

    def way(self, way):
        hw = way.tags.get("highway")
        if hw not in self.factors:
            return

        raw = way.tags.get("maxspeed")
        try:
            base = int(str(raw).split()[0])
        except (TypeError, ValueError):
            base = FREEFLOW[hw]

        spd = max(5, round(base * self.factors[hw]))
        oneway = way.tags.get("oneway") in ("yes", "true", "1")
        nodes = [n.ref for n in way.nodes]

        for a, b in zip(nodes, nodes[1:]):
            self.writer.writerow([a, b, spd, spd])
            self.rows += 1
            if not oneway:
                self.writer.writerow([b, a, spd, spd])
                self.rows += 1


def main() -> None:
    p = argparse.ArgumentParser(description="تولید CSV ترافیک برای osrm-customize")
    p.add_argument("--pbf", required=True, help="مسیر فایل .osm.pbf")
    p.add_argument("--hour", type=int, required=True, help="ساعت روز (0-23)")
    p.add_argument("--out", required=True, help="مسیر CSV خروجی")
    args = p.parse_args()

    if not 0 <= args.hour <= 23:
        p.error("--hour باید بین ۰ تا ۲۳ باشد")

    factors = factors_for_hour(args.hour)
    with open(args.out, "w", newline="") as f:
        handler = TrafficHandler(csv.writer(f), factors)
        handler.apply_file(args.pbf)

    print(f"{args.out}: {handler.rows} segment rows (hour={args.hour})")


if __name__ == "__main__":
    main()
