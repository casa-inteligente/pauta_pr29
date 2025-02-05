
function enableEditing() {
    document.querySelectorAll('.editable').forEach(element => {
        const field = element.getAttribute('data-field');
        const type = element.getAttribute('data-type');
        const value = element.textContent.trim();

        // Substituir por dropdown para 'regime'
        if (type === 'dropdown' && field === 'regime') {
            const options = {
                'PRE': 'Preventiva',
                'A': 'Alimentos',
                'PRO': 'Provisório',
                'F': 'Fechado',
                'SA': 'Semiaberto',
                'TOR': 'Tornozeleira'
            };
            const select = document.createElement('select');
            select.className = 'form-control';
            for (const [key, label] of Object.entries(options)) {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = label;
                if (label === value) option.selected = true;  // Usar o label para seleção correta
                select.appendChild(option);
            }
            element.innerHTML = '';
            element.appendChild(select);
        }

        // Substituir por dropdown para 'regime-aloc'
        else if (type === 'dropdown-aloc' && field === 'local_alocacao') {
            const options = {
                'TOR': 'Domiciliar',
                'F': 'Fechado',
                'SA': 'Semiaberto'
            };
            const select = document.createElement('select');
            select.className = 'form-control';
            for (const [key, label] of Object.entries(options)) {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = label;
                if (label === value) option.selected = true;  // Usar o label para seleção correta
                select.appendChild(option);
            }
            element.innerHTML = '';
            element.appendChild(select);
        }

        // Substituir por input de data para campos de data
        else if (type === 'date') {
            const input = document.createElement('input');
            input.type = 'date';
            input.className = 'form-control';
            // Converter formato dd/mm/yy para yyyy-mm-dd
            const [day, month, year] = value.split('/');
            input.value = `20${year}-${month}-${day}`;
            element.innerHTML = '';
            element.appendChild(input);
        }
        // Campos de texto normais (edição direta)
        else {
            element.contentEditable = true;
            element.style.backgroundColor = '#f8f9fa';
            element.style.border = '1px solid #ced4da';
        }
    });
}

function saveChanges() {
    const rows = document.querySelectorAll('tbody tr');
    const data = [];
    rows.forEach(row => {
        const rowData = { id: row.getAttribute('data-id') };
        row.querySelectorAll('.editable').forEach(cell => {
            const field = cell.getAttribute('data-field');
            const type = cell.getAttribute('data-type');
            let value;
            // Coletar valor do dropdown
            if (type === 'dropdown' || type === 'dropdown-aloc') {
                const select = cell.querySelector('select');
                value = select ? select.value : cell.textContent.trim();
            }
            // Coletar valor do input de data
            else if (type === 'date') {
                const input = cell.querySelector('input');
                if (input) {
                    value = input.value;  // yyyy-mm-dd
                } else {
                    value = cell.textContent.trim();
                }
            }
            // Coletar valor de texto normal
            else {
                value = cell.textContent.trim();
            }
            rowData[field] = value;
        });
        data.push(rowData);
    });

    // Enviar os dados para o servidor via AJAX
    fetch("{% url 'relação_detentos:salvar_alteracoes' %}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            console.log(result);
            if (result.success) {
                alert('Alterações salvas com sucesso!');
                location.reload(); // Recarregar a página para exibir os dados atualizados
            } else {
                alert('Erro ao salvar as alterações: ' + result.error);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao salvar as alterações.');
        });
}
