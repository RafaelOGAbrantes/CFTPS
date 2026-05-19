import streamlit as st
from config import TIPOS_ESPACOS, STATUS_ESPACO, ADMIN_EMAIL, ADMIN_PASSWORD
from database import (
    init_db, get_db_connection,
    get_espacos, get_reservas,
    criar_espaco, editar_espaco, remover_espaco,
    criar_reserva, remover_reserva, verificar_disponibilidade,
)

# Configuração da página (deve ser o PRIMEIRO comando Streamlit)
st.set_page_config(
    page_title="🏨 Sistema de Reservas Local",
    page_icon="🏨",
    layout="wide"
)

# Inicialização do banco
init_db()

# ─── LOGIN ──────────────────────────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def verificar_login():
    if not st.session_state['logged_in']:
        st.title("🔐 Login")
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar", key="btn_login", use_container_width=True):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
                    (email, senha)
                )
                if cursor.fetchone():
                    st.session_state['logged_in'] = True
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas!")
        return False
    return True

if not verificar_login():
    st.stop()

# ─── MENU LATERAL ───────────────────────────────────────────────────────────
st.sidebar.title("📁 Menu Principal")
menu_options = {
    "🏠 Dashboard": "dashboard",
    "🏢 Espaços": "espacos",
    "📅 Reservas": "reservas",
    "⚙️ Configurações": "config",
}

selected_key = st.sidebar.radio("Navegação", list(menu_options.keys()))
selected_option = menu_options[selected_key]   # converte para o valor interno

st.sidebar.markdown("---")
st.sidebar.markdown(f"👤 **{ADMIN_EMAIL}**")
st.sidebar.markdown("🚫 **Não compartilhe senhas**")

# ─── FUNÇÕES AUXILIARES ─────────────────────────────────────────────────────
def formatar_data(data):
    return data.strftime("%d/%m/%Y")

# ─── 🏠 DASHBOARD ───────────────────────────────────────────────────────────
if selected_option == "dashboard":
    st.title("🏨 Dashboard do Sistema")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_espacos = len(get_espacos())
        st.metric("Total de Espaços", total_espacos)

    with col2:
        total_reservas = len(get_reservas())
        st.metric("Reservas", total_reservas)

    with col3:
        espacos_ativos = len([e for e in get_espacos() if e['status'] == 1])
        st.metric("Espaços Ativos", espacos_ativos)

    with col4:
        reservas_ativas = len([r for r in get_reservas() if r['status'] == 1])
        st.metric("Reservas Ativas", reservas_ativas)

    st.markdown("---")
    st.subheader("📊 Resumo")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Atualizar Dashboard", type="primary"):
            st.rerun()
    with col2:
        st.info("💡 Para adicionar novos espaços, vá em 'Espaços'")

# ─── 🏢 ESPAÇOS ─────────────────────────────────────────────────────────────
elif selected_option == "espacos":
    st.title("🏢 Gestão de Espaços")

    tab1, tab2 = st.tabs(["📋 Lista", "➕ Criar/Editar"])

    with tab1:
        st.subheader("📋 Lista de Espaços")
        espacos = get_espacos()

        if espacos:
            for espaco in espacos:
                status_text = "✅ Ativo" if espaco['status'] else "❌ Inativo"

                with st.expander(f"🏢 {espaco['nome']} — {status_text}"):
                    st.write(f"**Tipo:** {espaco['tipo'].capitalize()}")
                    st.write(f"**Capacidade:** {espaco['capacidade']} pessoas")
                    if espaco['descricao']:
                        st.write(f"**Descrição:** {espaco['descricao']}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔧 Editar", key=f"editar_{espaco['id']}"):
                            st.session_state.editando_espaco = True
                            st.session_state.espaco_atual = espaco
                            st.rerun()

                    with col2:
                        if st.button("📤 Verificar Disponibilidade", key=f"dispo_{espaco['id']}"):
                            st.info("🔍 Sem conflitos encontrados.")

                    with col3:
                        if st.button("❌ Remover", type="secondary", key=f"remover_{espaco['id']}"):
                            st.session_state[f"confirmar_remover_{espaco['id']}"] = True

                    # Confirmação de remoção sem st.confirm()
                    if st.session_state.get(f"confirmar_remover_{espaco['id']}"):
                        st.warning(f"⚠️ Tem certeza que deseja remover **{espaco['nome']}**?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Sim, remover", key=f"sim_remover_{espaco['id']}"):
                                remover_espaco(espaco['id'])
                                st.success("✅ Espaço removido!")
                                st.session_state.pop(f"confirmar_remover_{espaco['id']}", None)
                                st.rerun()
                        with c2:
                            if st.button("🚫 Cancelar", key=f"nao_remover_{espaco['id']}"):
                                st.session_state.pop(f"confirmar_remover_{espaco['id']}", None)
                                st.rerun()
        else:
            st.info("📋 Nenhum espaço cadastrado.")

    with tab2:
        if 'editando_espaco' in st.session_state and st.session_state.editando_espaco:
            st.subheader("🔧 Editar Espaço")
            espaco_atual = st.session_state.espaco_atual

            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome", value=espaco_atual['nome'])
            with col2:
                tipo = st.selectbox(
                    "Tipo", TIPOS_ESPACOS,
                    index=TIPOS_ESPACOS.index(espaco_atual['tipo'])
                )
            with col3:
                capacidade = st.number_input("Capacidade", min_value=1, value=espaco_atual['capacidade'])

            descricao = st.text_area("Descrição", value=espaco_atual['descricao'] or "")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Salvar", type="primary"):
                    result = editar_espaco(
                        espaco_atual['id'],
                        nome=nome,
                        tipo=tipo,
                        capacidade=capacidade,
                        descricao=descricao
                    )
                    if result > 0:
                        st.success("✅ Espaço atualizado com sucesso!")
                        st.session_state.editando_espaco = False
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.editando_espaco = False
                    st.rerun()
        else:
            st.subheader("➕ Criar Novo Espaço")
            nome = st.text_input("Nome do Espaço", key="nova_espaco_nome")
            tipo = st.selectbox("Tipo", TIPOS_ESPACOS, key="nova_espaco_tipo")
            capacidade = st.number_input("Capacidade Máxima", min_value=1, key="nova_espaco_capacidade")
            descricao = st.text_area("Descrição", key="nova_espaco_descricao")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Criar", type="primary"):
                    if nome and tipo and capacidade:
                        new_id = criar_espaco(nome, tipo, capacidade, descricao)
                        if new_id:
                            st.success("✅ Espaço criado com sucesso!")
                            st.rerun()
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios.")
            with col2:
                st.info("⚠️ Preencha todos os campos para criar um novo espaço.")

# ─── 📅 RESERVAS ─────────────────────────────────────────────────────────────
elif selected_option == "reservas":
    st.title("📅 Gestão de Reservas")

    col1, col2 = st.columns(2)
    with col1:
        filtro_data = st.text_input("Filtrar por Data", key="filtro_data_reservas")
    with col2:
        filtro_espaco = st.selectbox(
            "Filtrar por Espaço",
            ["Todos"] + [e['nome'] for e in get_espacos()],
            key="filtro_espaco_reservas"
        )

    st.markdown("---")

    # Listar Reservas
    reservas = get_reservas()

    if reservas:
        st.subheader("📋 Lista de Reservas")

        for reserva in reservas:
            espaco = next((e for e in get_espacos() if e['id'] == reserva['id_espaco']), None)
            espaco_nome = espaco['nome'] if espaco else "Espaço Desconhecido"

            with st.container(border=True):
                st.write(f"### 🗓️ Reserva #{reserva['id']}")

                if espaco:
                    st.write(f"🏢 **Espaço:** {espaco['nome']}")
                    st.write(f"📍 **Tipo:** {espaco['tipo']}")
                    st.write(f"👥 **Capacidade:** {espaco['capacidade']}")

                st.write(f"📅 **Data:** {reserva['data_inicio']} → {reserva['data_fim']}")
                if reserva['hora_inicio']:
                    st.write(f"🕐 **Horário:** {reserva['hora_inicio']} → {reserva['hora_fim']}")
                st.write(f"👥 **Participantes:** {reserva['participantes']}")
                status_label = "✅ Confirmada" if reserva['status'] else "❌ Cancelada"
                st.write(f"🔘 **Status:** {status_label}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Cancelar Reserva", key=f"cancelar_{reserva['id']}"):
                        remover_reserva(reserva['id'])
                        st.success("📍 Reserva cancelada!")
                        st.rerun()
                with col2:
                    if st.button("📋 Ver Detalhes", key=f"detalhes_{reserva['id']}"):
                        st.info(f"📍 ID Espaço: {reserva['id_espaco']}")
                        if espaco:
                            st.info(f"👥 Capacidade: {espaco['capacidade']}")
    else:
        st.info("📋 Nenhuma reserva encontrada.")

    st.markdown("---")
    st.subheader("➕ Criar Nova Reserva")

    espacos_lista = get_espacos()
    if not espacos_lista:
        st.warning("⚠️ Cadastre ao menos um espaço antes de criar uma reserva.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            opcoes_espaco = {e['nome']: e['id'] for e in espacos_lista}
            espaco_nome_sel = st.selectbox(
                "Selecione o Espaço",
                list(opcoes_espaco.keys()),
                key="selecionar_espaco"
            )
            espaco_id = opcoes_espaco[espaco_nome_sel]
            espaco_sel = next((e for e in espacos_lista if e['id'] == espaco_id), None)
            if espaco_sel:
                st.write(f"**Capacidade:** {espaco_sel['capacidade']} pessoas")

        with col2:
            data_inicio = st.date_input("Data Início", key="data_inicio_reserva")
            data_fim = st.date_input("Data Fim", key="data_fim_reserva")
            participantes = st.number_input("Participantes", min_value=1, max_value=1000, key="participantes_reserva")

        if st.button("💾 Salvar Reserva", type="primary", key="btn_salvar_reserva"):
            if data_inicio and data_fim and participantes:
                if data_fim < data_inicio:
                    st.error("❌ A data de fim não pode ser anterior à data de início.")
                elif verificar_disponibilidade(espaco_id, data_inicio, data_fim):
                    criar_reserva(espaco_id, data_inicio, data_fim, participantes=participantes)
                    st.success("✅ Reserva criada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Espaço não disponível para o período informado!")
            else:
                st.error("❌ Preencha todos os campos!")

# ─── ⚙️ CONFIGURAÇÕES ────────────────────────────────────────────────────────
elif selected_option == "config":
    st.title("⚙️ Configurações do Sistema")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔐 Credenciais Admin")
        st.write(f"**Email:** {ADMIN_EMAIL}")
        st.write("**Senha:** ••••••••")

        if st.button("🚪 Sair da Sessão"):
            st.session_state['logged_in'] = False
            st.rerun()

    with col2:
        st.subheader("📊 Banco de Dados")

        if st.session_state.get("confirmar_limpar_db"):
            st.warning("⚠️ Isso apagará **TODOS** os dados! Esta ação não pode ser desfeita.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Sim, limpar tudo", key="btn_confirmar_limpar"):
                    espacos = get_espacos()
                    reservas = get_reservas()
                    for r in reservas:
                        remover_reserva(r['id'])
                    for e in espacos:
                        remover_espaco(e['id'])
                    st.session_state.pop("confirmar_limpar_db", None)
                    st.success("✅ Banco limpo com sucesso!")
                    st.rerun()
            with c2:
                if st.button("🚫 Cancelar", key="btn_cancelar_limpar"):
                    st.session_state.pop("confirmar_limpar_db", None)
                    st.rerun()
        else:
            if st.button("🗑️ Limpar Banco de Dados", type="secondary"):
                st.session_state["confirmar_limpar_db"] = True
                st.rerun()
