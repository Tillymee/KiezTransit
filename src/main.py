from src.lines.m2 import get_m2_am_steinberg


def print_m2():
    print("\n🚋 KiezTransit – M2 Abfahrten (Am Steinberg)\n")

    departures = get_m2_am_steinberg()

    if not departures:
        print("Keine Abfahrten gefunden.\n")
        return

    for d in departures:
        delay_txt = "pünktlich" if d["delay"] == 0 else f"+{d['delay']} min"
        print(f"M2 Richtung {d['direction']}")
        print(f"  → in {d['in_minutes']} min ({delay_txt})\n")


if __name__ == "__main__":
    print_m2()