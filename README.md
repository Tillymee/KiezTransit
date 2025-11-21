```
KiezTransit/
│
├── public/
│   ├── map.html
│   └── data/
│       ├── lines.json
│       ├── m2.json
│       └── (weitere Linien später: m10.json, u2.json ...)
│
├── scripts/
│   ├── build_line.py
│   └── helpers/
│       ├── fetch_stops.py
│       └── fetch_shape.py
│
└── src/
    ├── api/
    │   └── vbb.py
    │
    ├── lines/
    │   └── m2.py
    │
    └── ui/
        └── console.py

main.py (optional – muss nicht im Projektroot liegen)
```