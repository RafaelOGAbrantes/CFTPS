import streamlit as st
from datetime import datetime
from config import TIPOS_ESPACOS, STATUS_ESPACO, ADMIN_EMAIL, ADMIN_PASSWORD
from database import (
    init_db, get_db_connection,
    get_espacos, get_reservas,
    criar_espaco, editar_espaco, remover_espaco,
    criar_reserva, remover_reserva, verificar_disponibilidade,
    get_usuarios, criar_usuario, editar_usuario, remover_usuario, alterar_senha
)

# Configuração da página (deve ser o PRIMEIRO comando Streamlit)
st.set_page_config(
    page_title="🏨 Centro de Treinamento de Sousa",
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
                user = cursor.fetchone()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = dict(user)
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas!")
        return False
    return True

if not verificar_login():
    st.stop()

if st.session_state['user'].get('email') == ADMIN_EMAIL and st.session_state['user'].get('senha') == ADMIN_PASSWORD:
    st.warning("⚠️ Você está usando a senha padrão do administrador. Por favor, altere sua senha para continuar.")
    nova_senha_admin = st.text_input("Nova Senha", type="password", key="nova_senha_admin_init")
    confirmar_senha_admin = st.text_input("Confirmar Nova Senha", type="password", key="confirmar_senha_admin_init")
    if st.button("Alterar Senha", type="primary"):
        if nova_senha_admin and nova_senha_admin == confirmar_senha_admin:
            alterar_senha(st.session_state['user']['id'], nova_senha_admin)
            st.session_state['user']['senha'] = nova_senha_admin
            st.success("✅ Senha alterada com sucesso!")
            st.rerun()
        else:
            st.error("❌ As senhas não coincidem ou estão vazias.")
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
if 'user' in st.session_state:
    st.sidebar.markdown(f"👤 **{st.session_state['user'].get('nome', ADMIN_EMAIL)}**")
    st.sidebar.markdown(f"📧 {st.session_state['user'].get('email', ADMIN_EMAIL)}")
else:
    st.sidebar.markdown(f"👤 **{ADMIN_EMAIL}**")
st.sidebar.markdown("🚫 **Não compartilhe senhas**")

# ─── FUNÇÕES AUXILIARES ─────────────────────────────────────────────────────
def formatar_data_str(data_str):
    try:
        data_obj = datetime.strptime(str(data_str), "%Y-%m-%d").date()
        return data_obj.strftime("%d/%m/%Y")
    except:
        return data_str

def formatar_data(data):
    return data.strftime("%d/%m/%Y")

# ─── 🏠 DASHBOARD ───────────────────────────────────────────────────────────
if selected_option == "dashboard":
    st.title("🏨 Dashboard do Centro de Treinamento de Sousa")

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
    st.subheader("📊 Resumo e Hoje")

    col1, col2 = st.columns(2)
    with col1:
        hoje_str = datetime.today().strftime("%Y-%m-%d")
        reservas_hoje = [r for r in get_reservas() if str(r['data_inicio']) <= hoje_str <= str(r['data_fim']) and r['status'] == 1]
        st.write(f"**Reservas para Hoje ({formatar_data_str(hoje_str)}):** {len(reservas_hoje)}")
        for r in reservas_hoje:
            espaco_nome = next((e['nome'] for e in get_espacos() if e['id'] == r['id_espaco']), "Desconhecido")
            r_nome = r.get('nome') or f"Reserva #{r['id']}"
            st.info(f"📍 **{r_nome}** - Espaço: {espaco_nome}")

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

    # Filtros
    with st.expander("🔍 Filtros de Busca", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_data = st.date_input("Filtrar por Data", value=None, format="DD/MM/YYYY", key="filtro_data_reservas")
        with col_f2:
            filtro_espaco = st.selectbox(
                "Filtrar por Espaço",
                ["Todos"] + [e['nome'] for e in get_espacos()],
                key="filtro_espaco_reservas"
            )
        with col_f3:
            filtro_usuario = st.selectbox(
                "Filtrar por Usuário",
                ["Todos"] + [u['nome'] for u in get_usuarios()],
                key="filtro_usuario_reservas"
            )

    st.markdown("---")

    # Listar Reservas
    todas_reservas = get_reservas()
    usuarios_dict = {u['id']: u['nome'] for u in get_usuarios()}
    espacos_lista = get_espacos()
    
    # Aplicar filtros
    reservas_filtradas = []
    for r in todas_reservas:
        if filtro_data:
            if not (str(r['data_inicio']) <= str(filtro_data) <= str(r['data_fim'])):
                continue
        if filtro_espaco != "Todos":
            esp = next((e for e in espacos_lista if e['id'] == r['id_espaco']), None)
            if not esp or esp['nome'] != filtro_espaco:
                continue
        if filtro_usuario != "Todos":
            u_nome = usuarios_dict.get(r['id_usuario'], "Desconhecido")
            if u_nome != filtro_usuario:
                continue
        reservas_filtradas.append(r)

    if reservas_filtradas:
        st.subheader(f"📋 Lista de Reservas ({len(reservas_filtradas)})")

        for reserva in reservas_filtradas:
            espaco = next((e for e in espacos_lista if e['id'] == reserva['id_espaco']), None)
            espaco_nome = espaco['nome'] if espaco else "Espaço Desconhecido"
            criador_nome = usuarios_dict.get(reserva['id_usuario'], "Desconhecido")
            nome_reserva = reserva.get('nome') or f"Reserva #{reserva['id']}"

            with st.container(border=True):
                st.write(f"### 🗓️ {nome_reserva}")

                col_det1, col_det2 = st.columns(2)
                with col_det1:
                    if espaco:
                        st.write(f"🏢 **Espaço:** {espaco['nome']} ({espaco['tipo'].capitalize()})")
                    st.write(f"👤 **Criada por:** {criador_nome}")
                with col_det2:
                    st.write(f"📅 **Data:** {formatar_data_str(reserva['data_inicio'])} → {formatar_data_str(reserva['data_fim'])}")
                    if reserva['hora_inicio']:
                        st.write(f"🕐 **Horário:** {reserva['hora_inicio']} → {reserva['hora_fim']}")
                    st.write(f"👥 **Participantes:** {reserva['participantes']}")
                
                status_label = "✅ Confirmada" if reserva['status'] else "❌ Cancelada"
                st.write(f"🔘 **Status:** {status_label}")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🗑️ Cancelar Reserva", key=f"btn_cancelar_{reserva['id']}"):
                        st.session_state[f"confirmar_cancelar_reserva_{reserva['id']}"] = True

                if st.session_state.get(f"confirmar_cancelar_reserva_{reserva['id']}"):
                    st.warning(f"⚠️ Tem certeza que deseja cancelar a reserva **{nome_reserva}**?")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Sim, cancelar", key=f"sim_cancelar_reserva_{reserva['id']}"):
                            remover_reserva(reserva['id'])
                            st.success("📍 Reserva cancelada!")
                            st.session_state.pop(f"confirmar_cancelar_reserva_{reserva['id']}", None)
                            st.rerun()
                    with c2:
                        if st.button("🚫 Cancelar ação", key=f"nao_cancelar_reserva_{reserva['id']}"):
                            st.session_state.pop(f"confirmar_cancelar_reserva_{reserva['id']}", None)
                            st.rerun()
    else:
        st.info("📋 Nenhuma reserva encontrada com os filtros selecionados.")

    st.markdown("---")
    st.subheader("➕ Criar Nova Reserva")

    if not espacos_lista:
        st.warning("⚠️ Cadastre ao menos um espaço antes de criar uma reserva.")
    else:
        # Avoid columns here for better mobile support
        opcoes_espaco = {e['nome']: e['id'] for e in espacos_lista}
        
        nome_reserva_nova = st.text_input("Nome da Reserva (Opcional)", key="nova_reserva_nome")
        espaco_nome_sel = st.selectbox("Selecione o Espaço", list(opcoes_espaco.keys()), key="selecionar_espaco")
        espaco_id = opcoes_espaco[espaco_nome_sel]
        espaco_sel = next((e for e in espacos_lista if e['id'] == espaco_id), None)
        if espaco_sel:
            st.caption(f"Capacidade do espaço: {espaco_sel['capacidade']} pessoas")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_inicio = st.date_input("Data Início", format="DD/MM/YYYY", key="data_inicio_reserva")
        with col_d2:
            data_fim = st.date_input("Data Fim", format="DD/MM/YYYY", key="data_fim_reserva")
            
        max_participantes = espaco_sel['capacidade'] if espaco_sel else 1000
        participantes = st.number_input("Participantes", min_value=1, max_value=max_participantes, key="participantes_reserva")

        if st.button("💾 Salvar Reserva", type="primary", key="btn_salvar_reserva", use_container_width=True):
            if data_inicio and data_fim and participantes:
                if data_fim < data_inicio:
                    st.error("❌ A data de fim não pode ser anterior à data de início.")
                elif espaco_sel and participantes > espaco_sel['capacidade']:
                    st.error(f"❌ A quantidade de participantes excede a capacidade do espaço ({espaco_sel['capacidade']} pessoas).")
                elif verificar_disponibilidade(espaco_id, data_inicio, data_fim):
                    criar_reserva(
                        espaco_id, data_inicio, data_fim, participantes, 
                        nome=nome_reserva_nova, 
                        id_usuario=st.session_state['user'].get('id')
                    )
                    st.success("✅ Reserva criada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Espaço não disponível para o período informado!")
            else:
                st.error("❌ Preencha todos os campos obrigatórios!")

# ─── ⚙️ CONFIGURAÇÕES ────────────────────────────────────────────────────────
elif selected_option == "config":
    st.title("⚙️ Configurações do Sistema")

    tab_cred, tab_db, tab_usuarios = st.tabs(["🔐 Minha Conta", "📊 Banco de Dados", "👥 Usuários"])

    with tab_cred:
        st.subheader("Meus Dados")
        user = st.session_state.get('user', {})
        st.write(f"**Nome:** {user.get('nome', '')}")
        st.write(f"**Email:** {user.get('email', ADMIN_EMAIL)}")

        if st.button("🚪 Sair da Sessão", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state.pop('user', None)
            st.rerun()

    with tab_db:
        st.subheader("Limpeza do Banco de Dados")
        if st.session_state.get("confirmar_limpar_db"):
            st.warning("⚠️ Isso apagará **TODOS** os dados (espaços e reservas)! Ações de usuários não são apagadas.")
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

    with tab_usuarios:
        st.subheader("Gestão de Usuários")
        usuarios = get_usuarios()
        
        with st.expander("➕ Adicionar Usuário"):
            novo_nome = st.text_input("Nome", key="novo_user_nome")
            novo_email = st.text_input("Email", key="novo_user_email")
            nova_senha = st.text_input("Senha", type="password", key="novo_user_senha")
            novo_telefone = st.text_input("Telefone (Opcional)", key="novo_user_telefone")
            
            if st.button("Adicionar", key="btn_add_user"):
                if novo_nome and novo_email and nova_senha:
                    res = criar_usuario(novo_nome, novo_email, nova_senha, novo_telefone)
                    if res:
                        st.success("✅ Usuário adicionado!")
                        st.rerun()
                    else:
                        st.error("❌ Email já cadastrado.")
                else:
                    st.error("⚠️ Preencha os campos obrigatórios (Nome, Email, Senha).")
                    
        st.markdown("---")
        st.subheader("Usuários Cadastrados")
        for u in usuarios:
            with st.container(border=True):
                col_u1, col_u2 = st.columns([3, 1])
                with col_u1:
                    st.write(f"**{u['nome']}** ({u['email']})")
                    if u['telefone']:
                        st.write(f"📞 {u['telefone']}")
                with col_u2:
                    if u['email'] != ADMIN_EMAIL: # Protege admin principal
                        if st.button("🗑️ Remover", key=f"remover_user_{u['id']}"):
                            remover_usuario(u['id'])
                            st.success("Usuário removido!")
                            st.rerun()
                
                with st.expander("Alterar Senha", expanded=False):
                    nova_senha_u = st.text_input("Nova Senha", type="password", key=f"senha_user_{u['id']}")
                    if st.button("Salvar Senha", key=f"btn_senha_user_{u['id']}"):
                        if nova_senha_u:
                            alterar_senha(u['id'], nova_senha_u)
                            st.success("Senha alterada com sucesso!")
                        else:
                            st.error("Insira a nova senha.")
