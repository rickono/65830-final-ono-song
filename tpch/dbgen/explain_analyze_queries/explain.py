files = ['1.sql', '10.sql', '11.sql', '12.sql', '13.sql', '14.sql', '15.sql', '16.sql', '17.sql', '18.sql',
         '19.sql', '2.sql', '20.sql', '21.sql', '22.sql', '3.sql', '4.sql', '5.sql', '6.sql', '7.sql', '8.sql', '9.sql']

for file in files:
    content = ''
    with open(file, 'r') as f:
        content = f.read()
    with open(file, 'w') as f:
        f.write('explain analyze ' + content)
