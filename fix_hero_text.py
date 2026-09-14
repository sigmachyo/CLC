with open('/Users/valera/study/kclc/CLC/templates/library/home.html', 'r') as f:
    c = f.read()

start_marker = '<div class="relative z-30 px-6 sm:px-12 max-w-5xl text-center w-full mt-16 sm:mt-0">'
end_marker = '<!-- Контент библиотеки (Минимализм Bible.com) -->'

start_idx = c.find(start_marker)
end_idx = c.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_block = """<div class="relative z-30 px-6 sm:px-12 max-w-4xl text-center w-full mt-16 sm:mt-0 mx-auto">
        <h2 class="text-xs sm:text-sm font-bold text-white/50 mb-10 tracking-[0.3em] uppercase">Стих дня</h2>
        
        <p class="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-display font-semibold text-white leading-[1.2] mb-10 drop-shadow-2xl">
            {{ daily_verse.verse_text }}
        </p>
        
        <div class="flex items-center justify-center gap-6 mt-12">
            <div class="h-[2px] w-12 bg-primary/60 rounded-full"></div>
            <p class="text-primary font-bold text-lg sm:text-xl tracking-[0.15em] uppercase drop-shadow-md">
                {{ daily_verse.reference }}
            </p>
            <div class="h-[2px] w-12 bg-primary/60 rounded-full"></div>
        </div>
    </div>
</div>
{% else %}
<div class="pt-32"></div>
{% endif %}

"""
    c = c[:start_idx] + new_block + c[end_idx:]
    with open('/Users/valera/study/kclc/CLC/templates/library/home.html', 'w') as f:
        f.write(c)
else:
    print("Markers not found!")
