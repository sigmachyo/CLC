with open('/Users/valera/study/kclc/CLC/templates/library/home.html', 'r') as f:
    c = f.read()

# Make image z-0
c = c.replace('-z-20', 'z-0')
# Make overlay z-10
c = c.replace('-z-10', 'z-10')
# Make the gradient overlay z-20 (it was absolute inset-0 without z-index before)
c = c.replace('class="absolute inset-0 bg-gradient-to-t', 'class="absolute inset-0 z-20 bg-gradient-to-t')
# Make the text container z-30 (was z-10)
c = c.replace('class="relative z-10 px-6 sm:px-12', 'class="relative z-30 px-6 sm:px-12')
# Make the scroll indicator z-30 (was z-10)
c = c.replace('class="absolute bottom-10 left-1/2 transform -translate-x-1/2 z-10', 'class="absolute bottom-10 left-1/2 transform -translate-x-1/2 z-30')
# Make the library content wrapper z-30 (was z-10)
c = c.replace('class="relative z-10 w-full bg-[#0a0f18]"', 'class="relative z-30 w-full bg-[#0a0f18]"')

with open('/Users/valera/study/kclc/CLC/templates/library/home.html', 'w') as f:
    f.write(c)
