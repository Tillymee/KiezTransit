```
KiezTransit/
│
├── public/
│   ├── map.html
│   └── data/
│       ├── lines.json
│       └── <id>.line.json    (wird automatisch erzeugt)
│
├── config/
│   └── lines/
│       ├── m2.config.json
│       ├── u1.config.json
│       ├── s8.config.json
│       └── bus_255.config.json
│
├── scripts/
│   └── build_line.py
│
└── src/
    ├── api/
    │   └── vbb.py
    ├── ui/
    │   └── console.py
    └── lines/
        └── (optional weitere Live-Linienmodule)
```