with open('/Users/valera/study/kclc/CLC/templates/library/home.html', 'r') as f:
    c = f.read()

c = c.replace(
    'class="fixed top-0 left-0 right-0 bottom-0 w-full h-[100vh]',
    'class="absolute inset-0 w-full h-full'
)

with open('/Users/valera/study/kclc/CLC/templates/library/home.html', 'w') as f:
    f.write(c)
