import re

with open('templates/partials/library/podcast_section.html', 'r') as f:
    content = f.read()

# 1. Remove "Все подкасты" link
content = content.replace('<a href="{% url \'podcast_list\' %}" class="text-white/50 hover:text-white transition-colors text-sm font-medium">Все подкасты</a>', '')

# 2. Re-arrange HTML structure to be Row 1 (Header) and Row 2 (Playlist).
# Currently .ym-layout wraps BOTH .ym-cover-col and .ym-info-col, and .ym-info-col wraps BOTH .ym-album-info and .ym-playlist-container.
# We will make .ym-info-col only hold the header info, and move .ym-playlist-container outside .ym-layout, or just change the CSS so it flows naturally.

# CSS Replacements
css_replacements = {
    # Desktop layout
    '.ym-layout {\n    display: flex;\n    flex-direction: row;\n    gap: 40px;\n    padding: 0;\n    min-width: 0;\n}': 
    '.ym-layout {\n    display: flex;\n    flex-direction: row;\n    align-items: center;\n    gap: 20px;\n    padding: 0;\n    min-width: 0;\n    margin-bottom: 24px;\n}',
    
    # Cover column desktop
    '.ym-cover-col {\n    flex: 0 0 300px;\n}': 
    '.ym-cover-col {\n    flex: 0 0 120px;\n}',
    
    '.ym-cover {\n    width: 100%;\n    aspect-ratio: 1 / 1;\n    max-width: 300px;':
    '.ym-cover {\n    width: 120px;\n    height: 120px;\n    flex-shrink: 0;',

    # Mobile overrides
    '.ym-cover {\n        width: 160px;\n        height: 160px;\n    }':
    '.ym-cover {\n        width: 100px;\n        height: 100px;\n    }',
    
    # Remove flex-direction: column on mobile so they stay inline
    '.ym-layout {\n        flex-direction: column;\n        padding: 0; /* Minimal */\n        gap: 24px;\n    }':
    '.ym-layout {\n        flex-direction: row;\n        padding: 0;\n        gap: 16px;\n        align-items: center;\n    }',
    
    '.ym-cover-col {\n        display: flex;\n        justify-content: center;\n        flex: none;\n    }':
    '.ym-cover-col {\n        flex: 0 0 100px;\n    }',
    
    '.ym-album-title {\n        font-size: 1.5rem;\n        text-align: center;\n    }':
    '.ym-album-title {\n        font-size: 1.25rem;\n        text-align: left;\n    }',
    
    '.ym-album-meta {\n        text-align: center;\n        margin-bottom: 20px;\n    }':
    '.ym-album-meta {\n        text-align: left;\n        margin-bottom: 12px;\n    }',
    
    # Make Desktop playlist horizontal as well to save space
    '.ym-playlist {\n    display: flex;\n    flex-direction: column;\n    gap: 2px;\n    overflow-y: auto;\n    max-height: 400px;\n    padding-right: 12px;\n}':
    '.ym-playlist {\n    display: flex;\n    flex-direction: row;\n    gap: 12px;\n    overflow-x: auto;\n    overflow-y: hidden;\n    scroll-snap-type: x mandatory;\n    scrollbar-width: none;\n    margin: 0 -16px;\n    padding: 12px 16px 24px 16px;\n}',
    
    '.ym-track {\n    display: flex;\n    align-items: center;\n    gap: 16px;\n    padding: 12px 16px;\n    border-radius: 12px;\n    background: transparent;\n    border: 1px solid transparent;\n    cursor: pointer;\n    transition: all 0.2s ease;\n    text-align: left;\n    color: rgba(255,255,255,0.7);\n}':
    '.ym-track {\n    display: flex;\n    align-items: center;\n    gap: 16px;\n    padding: 16px;\n    border-radius: 16px;\n    background: rgba(255,255,255,0.05);\n    border: 1px solid rgba(255,255,255,0.05);\n    cursor: pointer;\n    transition: all 0.2s ease;\n    text-align: left;\n    color: rgba(255,255,255,0.7);\n    flex: 0 0 clamp(220px, 70vw, 300px);\n    scroll-snap-align: center;\n}',
    
    '.ym-btn-main {\n        width: 100%;\n        justify-content: center;\n    }':
    '.ym-btn-main {\n        width: auto;\n    }',

    # Also move the playlist container out of .ym-info-col structurally so it takes full width
}

# 1. Structural change: 
# Find: <div class="ym-playlist-container"> and the end of .ym-info-col
# Currently: 
# <div class="ym-info-col">
#   <div class="ym-album-info">...</div>
#   <div class="ym-playlist-container">...</div>
# </div>

# Replace with:
# <div class="ym-info-col">
#   <div class="ym-album-info">...</div>
# </div>
# </div> <!-- End of ym-layout -->
# <div class="ym-playlist-container">...</div>

html_old = '''                </div>

                <div class="ym-playlist-container">
                    <div class="ym-playlist-header desktop-only">'''
                    
html_new = '''                </div>
            </div>
        </div> <!-- End ym-layout -->

        <div class="ym-playlist-container">
            <div class="ym-playlist-header desktop-only" style="display:none;">'''
content = content.replace(html_old, html_new)

# And fix the closing tags that we shifted
end_old = '''                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>'''
end_new = '''                        {% endfor %}
                    </div>
                </div>
            <!-- layout was closed above -->'''
content = content.replace(end_old, end_new)


# Apply CSS replacements
for old, new in css_replacements.items():
    content = content.replace(old, new)

with open('templates/partials/library/podcast_section.html', 'w') as f:
    f.write(content)

print("Updated podcast_section.html layout")
