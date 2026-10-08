Mergeie a branch insert-mutations em todas as branches de mutação aqui (5 no total) e faça push.

Regras:
1. Antes de tudo, verifique: working tree limpa, quais branches existem
   localmente/remotamente, e rode `git merge-tree` para simular cada merge
   e me mostrar quais teriam conflito (arquivo + linha).
2. Se houver conflito, NÃO resolva sozinho — me mostre os dois lados
   (ours vs theirs) e pergunte qual prevalece.
3. Se uma branch só existir no remoto, crie tracking local antes.
4. Commit de merge com mensagem padrão do git. Sem rebase, sem force push.
5. Ao final, volte para a branch em que eu estava e confirme que
   local == origin em todas as alvos.
