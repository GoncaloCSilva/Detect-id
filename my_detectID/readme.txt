# Documentação do Projeto

    ## Base de Dados

## Instalação da Base de Dados no Django
Para configurar o projeto, segue estes passos:
1. Correr py manage.py makemigrations e migrate antes disto tudo!!!
2. Correr os codigos insert e keys que dizem "Modificados"
3. Correr o ficheiro teste.ipynb todo (isto obviamente tem de mudar, mas por enquanto fica)
    3.1 O ficheiro irá carregar os dados do excel nas tabelas postgreSQL
4. Na shell do Django correr os seguintes comandos:
    4.1 psql -U postgres  (ligar a Base de Dados, pede password, está nas settings)
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

(ATENÇÃO -> Isto tem que ser tudo mudado, ainda está numa versão muito pouco cuidadosa)


