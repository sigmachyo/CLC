import re

with open('templates/partials/library/podcast_section.html', 'r') as f:
    content = f.read()

# Make player flush with the library grid and minimal
content = content.replace(
    'max-width: 1000px;',
    'max-width: 100%;'
).replace(
    'background: rgba(255,255,255,0.03);',
    'background: transparent;'
).replace(
    'border: 1px solid rgba(255,255,255,0.15);',
    'border: none;'
).replace(
    'box-shadow: 0 20px 50px rgba(0,0,0,0.5);',
    'box-shadow: none;'
).replace(
    'padding: 40px;',
    'padding: 0;' # Desktop padding 0, layout gap handles spacing
)

# Mobile padding adjustments
content = content.replace(
    'padding: 24px 24px 0 24px; /* Убрал нижний отступ */',
    'padding: 0; /* Minimal */'
).replace(
    'padding: 12px 24px 24px 24px; /* Отступы для теней и скролла */',
    'padding: 12px 0 24px 0;'
).replace(
    'margin: 0 -24px; /* Растягиваем за пределы padding контейнера */',
    'margin: 0 -16px; padding: 12px 16px 24px 16px;'
)

# And player bar padding
content = content.replace(
    'padding: 20px 40px;',
    'padding: 20px 0;'
).replace(
    '.ym-player-bar {\n        padding: 0 24px;\n    }',
    '.ym-player-bar {\n        padding: 0;\n    }'
)

with open('templates/partials/library/podcast_section.html', 'w') as f:
    f.write(content)
print("Updated podcast styles")
