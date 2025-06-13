# **Trabalho Prático de Engenharia de Software 2**
## Integrantes
Giovana Piorino Vieira de Carvalho 

Matheus Galdino Ferreira

## Explicação do sistema

Nosso sistema se trata de uma simples plataforma para que músicos independentes/alternativos possam divulgar suas músicas. Nele temos dois perfis de usuário: artista e usuário comum. Um artista utiliza a conta para divulgar seu trabalho e avaliar opiniões de usuários sobre suas músicas, enquanto que um usuário pode navegar por músicas de difernetes estilos musicais, recebendo limks do YouTube para ouvir as músicas, dar opiniões sobre elas, bem como dar opiniões para artistas específicos como forma de feedback, além de dar likes em músicas específicas e artistas. O intuito é conectar pessoas dispostas e interessadas em músicos desconhecidos, independentes, e amadores, bem como divulgar os mesmos e prover uma plataforma de feedback de ouvintes. O trabalho ainda encontra-se em andamento, nem todos os requisitos planjeados foram implementados, mas o escopo geral do projeto já está definido. 

Ao chegar na página inicial, qualquer visitante pode optar por criar um perfil de artista, fornecendo um nome artístico e uma breve biografia, ou cadastrar-se como usuário. Artistas, uma vez logados, têm à disposição um painel onde adicionam novas faixas ao catálogo, definindo título, descrição e gênero, e podem voltar depois para atualizar essas informações sempre que desejarem. Do lado do ouvinte temos que: usuários autenticados podem navegar por gêneros, fazendo buscas temáticas que filtram apenas as músicas de sua preferência; podem ainda ver um ranking das faixas e perfis mais curtidos pela comunidade; e, é claro, interagir diretamente curtindo ou descurtindo tanto músicas quanto os próprios artistas. Tudo isso fica registrado para acesso futuro em uma seção pessoal de curtidas. O sistema mantém o estado de cada visitante (se é artista ou ouvinte e quais filtros aplicou) entre páginas. A persistência de dados cuida de armazenar perfis, músicas, gostos e opiniões, possibilitando relatórios de popularidade e históricos de navegação. 

## Instruções para utilizar o sistema

Para executar o programa, certifique-se de ter instalado localmente tanto o Flask como o SQLite, através dos comandos:

**pip install flask**

**sudo apt install sqlite3**

Após a instalação, navegue até o diretório raiz do repositório e execute o programa com o comando:

**python3 app.py**

O programa será inicializado e pode ser acessado através do navegador pelo endereço informado no terminal pelo framework. Para encerrar o programa, use Ctrl + C no terminal.

## Explicação das tecnologias utilizadas

O trabalho foi implementado em Python, usando Flask como framework web, HTML e CSS para interface web e estilização. Para persistência, adotamos SQLite (arquivo data.db), acessado via sqlite3. A suíte de testes foi construída com pytest. O gerenciamento de dependências é feito com pip/requirements.txt, o código versionado em Git e integrado continuamente via GitHub Actions.
