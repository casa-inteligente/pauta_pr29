// Função para emitir bip e mantê-lo ativo por 10 segundos
function bip() {
    var audio = new Audio('/static/compromissos/audio/beep-17.wav');
    audio.volume = 0.8;
    audio.loop = true;  // Ativar o loop
    audio.play();
    // Desativar o bip após 10 segundos
    setTimeout(function () {
        audio.pause();
    }, 5000);  // 5 segundos = 5000 milissegundos
}

// Função para verificar os horários dos compromissos
function verificarHorarios() {
    const compromissos = document.querySelectorAll('.compromisso');
    const now = new Date();

    compromissos.forEach(compromisso => {
        const compromissoData = new Date(compromisso.dataset.horario);
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
