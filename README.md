# pauta_pr29
criação de uma pauta virtual para o Presídio Regional de Maravilha.


### Lista de tarefas

 - [x]  Implementar banco de dados 🕠 :50:
 - [x]  Criação de um programa para mostrar no plano de fundo da estação de trabalho 👆
 - [ ]  Criação de um app android para monstrar a pauta :zzz:
 - [ ]  Criar uma animação para proteção de tela com a pauta 🪟 :zzz:

### Nome do banco de dados:  



 > [!NOTE]
 > Todos podem adicionar na pauta; </br>
 > Opção de alerta;


### Para iniciar o projeto
* ```django-admin startproject projeto_pauta```

* inicio do banco de dados, habilita a criação do superusuario
```python manage.py migrate```

* Criar um superusuario
```python manage.py createsuperuser``` <br>
-- solicita Nome; e-mail e senha

#### Passos para criação dos app's

* inicialização do app
```python manage.py startapp pauta```
>[!IMPORTANT]
> Cada alteração no banco de dados deverá, restabelecer as conexões; <br>
> Com os comandos abaixo;

* Criação do banco de dados para o app (pauta)
```python manage.py makemigrations pauta```
* Aplica as mudanças necessarias
``` python manage.py migrate```

>[!IMPORTANT]
> Deve-se mapear os arquivos estaticos
```python manage.py collectstatic```

## Deverá reiniciar o servidor
>[!WARNING]
> ``` sudo supervisorctl restart projeto_pauta ``` <br>
> ```sudo systemctl restart apache2 ```



## Rodando testes
```python manage.py test pauta.tests``` <br>
* Testes com o __coverage__
```coverage run --source='.' manage.py test pauta.tests``` <br>
```coverage report``` exibe no terminal os testes <br>
```coverage html``` Cria uma página web para visualização dos testes <br>



<br>

https://weareoutman.github.io/clockpicker/