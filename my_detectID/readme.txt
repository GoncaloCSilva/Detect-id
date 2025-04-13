# Documentação do Projeto

    ## Base de Dados

## Instalação da Base de Dados no Django
Para configurar o projeto, segue estes passos:
1. Correr py manage.py makemigrations e migrate antes disto tudo!!!
2. Correr os codigos insert e keys que dizem "Modificados"
3. Correr o ficheiro teste.ipynb todo (isto obviamente tem de mudar, mas por enquanto fica)
    3.1 O ficheiro irá carregar os dados do excel nas tabelas postgreSQL
4. Na shell do postgreSQL correr os seguintes comandos:
    4.1 psql -U postgres e \c detectid  (ligar a Base de Dados, pede password, está nas settings) 
    4.2 Certificar que as tabelas estão bem - \dt cdmdatabaseschema.*
    4.3 ALTER TABLE cdmdatabaseschema.person ADD COLUMN first_name VARCHAR(100); (4.3 e 4.4 é temporario)
    4.4 ALTER TABLE cdmdatabaseschema.person ADD COLUMN last_name VARCHAR(100);
    4.5 Verificar se as alterações foram feitas \d cdmdatabaseschema.person
    4.6 UPDATE cdmdatabaseschema.person AS p
        SET first_name = pd.first_name,
            last_name = pd.last_name
        FROM cdmdatabaseschema.person_details AS pd
        WHERE p.person_id = pd.person_id;
    4.7 DROP TABLE cdmdatabaseschema.person_details;


## Atualizar Tabela person com birthday
1. No terminal do postgres correr -> ALTER TABLE cdmdatabaseschema.person ADD COLUMN birthday DATE;
2. Correr na shell do django o seguinte codigo:
    from datetime import date^M
        ...: from utentes.models import Person
        ...: ^M
        ...: # Supondo que você tenha um queryset de pessoas^M
        ...: pessoas = Person.objects.all()
        ...: for p in pessoas:^M
        ...:     if p.year_of_birth and p.month_of_birth and p.day_of_birth:^M
        ...:         try:^M
        ...:             # Tente criar a data de nascimento^M
        ...:             p.birthday = date(p.year_of_birth, p.month_of_birth, p.day_of_birth)^M
        ...:             p.save()^M
        ...:         except Exception as e:^M
        ...:             # Captura erros, se houver^M
        ...:             print(f"Erro ao salvar data de nascimento para {p.id}: {e}")
        
(ATENÇÃO -> Isto tem que ser tudo mudado, ainda está numa versão muito pouco cuidadosa)


