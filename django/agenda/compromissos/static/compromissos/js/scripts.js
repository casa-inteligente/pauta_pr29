// Função para emitir bip e mantê-lo ativo por 10 segundos
function bip() {
    var audio = new Audio('/static/compromissos/audio/beep-17.wav');
    audio.volume = 0.8;
    audio.loop = true;  // Ativar o loop
    audio.play();
    // Desativar o bip após 10 segundos
    setTimeout(function () {
        audio.pause();
    }, 10000);  // 10 segundos = 10000 milissegundos
}

// Função para verificar os horários dos compromissos e tachar os passados
function verificarHorarios() {
    const compromissos = document.querySelectorAll('.compromisso');
    const now = new Date();

    compromissos.forEach(compromisso => {
        const compromissoData = new Date(compromisso.dataset.horario);

        // Tachar compromissos passados
        if (compromissoData < now) {
            compromisso.classList.add('text-muted');  // Classe do Bootstrap para texto acinzentado
            compromisso.style.textDecoration = 'line-through';  // Adiciona o tache
        }

        // Verificar se o compromisso é agora para emitir bip
        if (now.getFullYear() === compromissoData.getFullYear() &&
            now.getMonth() === compromissoData.getMonth() &&
            now.getDate() === compromissoData.getDate() &&
            now.getHours() === compromissoData.getHours() &&
            now.getMinutes() === compromissoData.getMinutes()) {
            bip();
        }
    });
}

// Verificar os horários a cada minuto
setInterval(verificarHorarios, 60000);

// Executar a função imediatamente ao carregar a página
verificarHorarios();
