with open('/Users/valera/study/kclc/CLC/templates/library/home.html', 'r') as f:
    c = f.read()

# 1. Change absolute to fixed, inset-0 to top-0 left-0 right-0 bottom-0, h-full to h-[100vh]
c = c.replace(
    'class="absolute inset-0 w-full h-full bg-cover bg-center transition-transform duration-[20000ms] hover:scale-105"',
    'class="fixed top-0 left-0 right-0 bottom-0 w-full h-[100vh] bg-cover bg-center transition-transform duration-[20000ms] hover:scale-105 -z-20"'
)

# 2. Fix the overlays to be fixed as well so they cover the background perfectly and don't scroll
c = c.replace(
    '<div class="absolute inset-0 bg-black/40"></div>',
    '<div class="fixed top-0 left-0 right-0 bottom-0 w-full h-[100vh] bg-black/40 -z-10"></div>'
)

# 3. Add solid background to the library categories wrapper so they cover the fixed background when scrolling
c = c.replace(
    '<div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 pb-32">',
    '<div class="relative z-10 w-full bg-[#0a0f18]"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 pb-32">'
)

# Close the new div at the end before {% endblock %}
c = c.replace(
    '</div>\n{% endblock %}',
    '</div></div>\n{% endblock %}'
)

with open('/Users/valera/study/kclc/CLC/templates/library/home.html', 'w') as f:
    f.write(c)
