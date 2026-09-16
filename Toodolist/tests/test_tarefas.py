from tests.conftest import login


def test_home_requires_login(client):
    response = client.get("/tarefas/", follow_redirects=False)
    assert response.status_code == 302


def test_create_tarefa_via_post(client, make_user, get_tarefas):
    user = make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    response = client.post(
        "/tarefas/",
        data={"tarefa": "Comprar pão", "descricao": "padaria da esquina"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    tarefas = get_tarefas(user.id)
    assert len(tarefas) == 1
    assert tarefas[0]["tarefa"] == "Comprar pão"
    assert tarefas[0]["status"] == "pendente"


def test_home_lists_only_current_user_tarefas(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    outro = make_user(nome="outro", senha="senha1234")
    make_tarefa(dono.id, tarefa="Tarefa do dono")
    make_tarefa(outro.id, tarefa="Tarefa do outro")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/")

    assert b"Tarefa do dono" in response.data
    assert b"Tarefa do outro" not in response.data


def test_search_filters_by_query(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Lavar o carro")
    make_tarefa(dono.id, tarefa="Estudar Python")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?q=carro")

    assert b"Lavar o carro" in response.data
    assert b"Estudar Python" not in response.data


def test_filter_by_status(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Pendente aqui", status="pendente")
    make_tarefa(dono.id, tarefa="Concluida aqui", status="concluido")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?filtro=concluidas")

    assert b"Concluida aqui" in response.data
    assert b"Pendente aqui" not in response.data


def test_filter_by_pendentes(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Pendente aqui", status="pendente")
    make_tarefa(dono.id, tarefa="Concluida aqui", status="concluido")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?filtro=pendentes")

    assert b"Pendente aqui" in response.data
    assert b"Concluida aqui" not in response.data


def test_filter_by_em_andamento(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Em andamento aqui", status="em_andamento")
    make_tarefa(dono.id, tarefa="Pendente aqui", status="pendente")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?filtro=em_andamento")

    assert b"Em andamento aqui" in response.data
    assert b"Pendente aqui" not in response.data


def test_filter_by_aguardando_retorno(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Aguardando aqui", status="aguardando_retorno")
    make_tarefa(dono.id, tarefa="Pendente aqui", status="pendente")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?filtro=aguardando_retorno")

    assert b"Aguardando aqui" in response.data
    assert b"Pendente aqui" not in response.data


def test_filter_by_canceladas(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Cancelada aqui", status="cancelado")
    make_tarefa(dono.id, tarefa="Pendente aqui", status="pendente")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?filtro=canceladas")

    assert b"Cancelada aqui" in response.data
    assert b"Pendente aqui" not in response.data


def test_alterar_status_toggles(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    login(client, "dono", "senha1234")
    client.post(f"/tarefas/alterar-status/{tarefa.id}")

    tarefas = get_tarefas(dono.id)
    assert tarefas[0]["status"] == "concluido"

    client.post(f"/tarefas/alterar-status/{tarefa.id}")
    tarefas = get_tarefas(dono.id)
    assert tarefas[0]["status"] == "pendente"


def test_alterar_status_completes_from_any_open_status(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="aguardando_retorno")

    login(client, "dono", "senha1234")
    client.post(f"/tarefas/alterar-status/{tarefa.id}")

    assert get_tarefas(dono.id)[0]["status"] == "concluido"


def test_editar_tarefa_updates_status(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    login(client, "dono", "senha1234")
    client.post(
        f"/tarefas/editar-tarefa/{tarefa.id}",
        data={"tarefa": "Nome", "descricao": "Desc", "status": "aguardando_retorno"},
    )

    assert get_tarefas(dono.id)[0]["status"] == "aguardando_retorno"


def test_editar_tarefa_ignores_invalid_status(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    login(client, "dono", "senha1234")
    client.post(
        f"/tarefas/editar-tarefa/{tarefa.id}",
        data={"tarefa": "Nome", "descricao": "Desc", "status": "status-forjado"},
    )

    assert get_tarefas(dono.id)[0]["status"] == "pendente"


def test_excluir_tarefa_removes_it(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id)

    login(client, "dono", "senha1234")
    client.post(f"/tarefas/excluir-tarefa/{tarefa.id}")

    assert get_tarefas(dono.id) == []


def test_editar_tarefa_updates_fields(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, tarefa="Nome antigo", descricao="Desc antiga")

    login(client, "dono", "senha1234")
    client.post(
        f"/tarefas/editar-tarefa/{tarefa.id}",
        data={"tarefa": "Nome novo", "descricao": "Desc nova"},
    )

    tarefas = get_tarefas(dono.id)
    assert tarefas[0]["tarefa"] == "Nome novo"
    assert tarefas[0]["descricao_obj"] == "Desc nova"


def test_cannot_alter_status_of_another_users_tarefa(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    atacante = make_user(nome="atacante", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    login(client, "atacante", "senha1234")
    response = client.post(f"/tarefas/alterar-status/{tarefa.id}", follow_redirects=True)

    assert b"Tarefa inexistente" in response.data
    tarefas = get_tarefas(dono.id)
    assert tarefas[0]["status"] == "pendente"


def test_cannot_delete_another_users_tarefa(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    atacante = make_user(nome="atacante", senha="senha1234")
    tarefa = make_tarefa(dono.id)

    login(client, "atacante", "senha1234")
    response = client.post(f"/tarefas/excluir-tarefa/{tarefa.id}", follow_redirects=True)

    assert b"Tarefa inexistente" in response.data
    assert len(get_tarefas(dono.id)) == 1


def test_cannot_edit_another_users_tarefa(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    atacante = make_user(nome="atacante", senha="senha1234")
    tarefa = make_tarefa(dono.id, tarefa="Original")

    login(client, "atacante", "senha1234")
    response = client.post(
        f"/tarefas/editar-tarefa/{tarefa.id}",
        data={"tarefa": "Hackeado", "descricao": "x"},
        follow_redirects=True,
    )

    assert b"Tarefa inexistente" in response.data
    tarefas = get_tarefas(dono.id)
    assert tarefas[0]["tarefa"] == "Original"


def test_create_tarefa_with_prioridade(client, make_user, get_tarefas):
    user = make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    client.post(
        "/tarefas/",
        data={"tarefa": "Tarefa urgente", "descricao": "x", "prioridade": "alta"},
        follow_redirects=True,
    )

    tarefas = get_tarefas(user.id)
    assert tarefas[0]["prioridade"] == "alta"


def test_create_tarefa_defaults_to_media_prioridade(client, make_user, get_tarefas):
    user = make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    client.post(
        "/tarefas/",
        data={"tarefa": "Tarefa qualquer", "descricao": "x"},
        follow_redirects=True,
    )

    tarefas = get_tarefas(user.id)
    assert tarefas[0]["prioridade"] == "media"


def test_create_tarefa_ignores_invalid_prioridade(client, make_user, get_tarefas):
    user = make_user(nome="dono", senha="senha1234")
    login(client, "dono", "senha1234")

    client.post(
        "/tarefas/",
        data={"tarefa": "Tarefa qualquer", "descricao": "x", "prioridade": "urgentissima"},
        follow_redirects=True,
    )

    tarefas = get_tarefas(user.id)
    assert tarefas[0]["prioridade"] == "media"


def test_editar_tarefa_updates_prioridade(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, prioridade="baixa")

    login(client, "dono", "senha1234")
    client.post(
        f"/tarefas/editar-tarefa/{tarefa.id}",
        data={"tarefa": "Nome", "descricao": "Desc", "status": "pendente", "prioridade": "alta"},
    )

    assert get_tarefas(dono.id)[0]["prioridade"] == "alta"


def test_editar_tarefa_ignores_invalid_prioridade(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, prioridade="baixa")

    login(client, "dono", "senha1234")
    client.post(
        f"/tarefas/editar-tarefa/{tarefa.id}",
        data={"tarefa": "Nome", "descricao": "Desc", "status": "pendente", "prioridade": "forjada"},
    )

    assert get_tarefas(dono.id)[0]["prioridade"] == "baixa"


def test_ordenar_por_data(client, make_user, make_tarefa):
    from datetime import datetime, timedelta

    dono = make_user(nome="dono", senha="senha1234")
    agora = datetime.now()
    make_tarefa(dono.id, tarefa="Mais antiga", created_at=agora - timedelta(days=2))
    make_tarefa(dono.id, tarefa="Mais recente", created_at=agora)

    login(client, "dono", "senha1234")

    response = client.get("/tarefas/?ordenar=data&direcao=asc")
    body = response.data.decode()
    assert body.index("Mais antiga") < body.index("Mais recente")

    response = client.get("/tarefas/?ordenar=data&direcao=desc")
    body = response.data.decode()
    assert body.index("Mais recente") < body.index("Mais antiga")


def test_ordenar_por_prioridade(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Tarefa baixa", prioridade="baixa")
    make_tarefa(dono.id, tarefa="Tarefa alta", prioridade="alta")
    make_tarefa(dono.id, tarefa="Tarefa media", prioridade="media")

    login(client, "dono", "senha1234")

    response = client.get("/tarefas/?ordenar=prioridade&direcao=desc")
    body = response.data.decode()
    assert body.index("Tarefa alta") < body.index("Tarefa media") < body.index("Tarefa baixa")

    response = client.get("/tarefas/?ordenar=prioridade&direcao=asc")
    body = response.data.decode()
    assert body.index("Tarefa baixa") < body.index("Tarefa media") < body.index("Tarefa alta")


def test_filter_by_prioridade(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Tarefa alta", prioridade="alta")
    make_tarefa(dono.id, tarefa="Tarefa baixa", prioridade="baixa")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?prioridade=alta")

    assert b"Tarefa alta" in response.data
    assert b"Tarefa baixa" not in response.data


def test_filter_by_status_and_prioridade_combined(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Pendente alta", status="pendente", prioridade="alta")
    make_tarefa(dono.id, tarefa="Pendente baixa", status="pendente", prioridade="baixa")
    make_tarefa(dono.id, tarefa="Concluida alta", status="concluido", prioridade="alta")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?filtro=pendentes&prioridade=alta")

    assert b"Pendente alta" in response.data
    assert b"Pendente baixa" not in response.data
    assert b"Concluida alta" not in response.data


def test_fixar_tarefa_toggles(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id)

    login(client, "dono", "senha1234")
    client.post(f"/tarefas/fixar-tarefa/{tarefa.id}")

    assert get_tarefas(dono.id)[0]["fixada"] is True

    client.post(f"/tarefas/fixar-tarefa/{tarefa.id}")
    assert get_tarefas(dono.id)[0]["fixada"] is False


def test_cannot_fixar_another_users_tarefa(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    atacante = make_user(nome="atacante", senha="senha1234")
    tarefa = make_tarefa(dono.id)

    login(client, "atacante", "senha1234")
    response = client.post(f"/tarefas/fixar-tarefa/{tarefa.id}", follow_redirects=True)

    assert b"Tarefa inexistente" in response.data
    assert get_tarefas(dono.id)[0]["fixada"] is False


def test_filter_by_fixadas(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Fixada aqui", fixada=True)
    make_tarefa(dono.id, tarefa="Solta aqui", fixada=False)

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?fixadas=1")

    assert b"Fixada aqui" in response.data
    assert b"Solta aqui" not in response.data


def test_tarefa_fixada_aparece_primeiro_independente_da_ordenacao(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="Normal recente")
    make_tarefa(dono.id, tarefa="Fixada antiga", fixada=True)

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?ordenar=data&direcao=desc")
    body = response.data.decode()

    assert body.index("Fixada antiga") < body.index("Normal recente")


def test_status_pills_show_counts_per_status(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    make_tarefa(dono.id, tarefa="P1", status="pendente")
    make_tarefa(dono.id, tarefa="P2", status="pendente")
    make_tarefa(dono.id, tarefa="C1", status="concluido")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/")
    body = response.data.decode()

    assert "pill-count" in body
    pendentes_idx = body.index("Pendentes <span")
    assert ">2<" in body[pendentes_idx:pendentes_idx + 100]


def test_alterar_status_preserves_active_filter(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    login(client, "dono", "senha1234")
    response = client.post(
        f"/tarefas/alterar-status/{tarefa.id}?filtro=pendentes",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "filtro=pendentes" in response.headers["Location"]


def test_fixar_tarefa_preserves_active_filter_and_ordering(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    login(client, "dono", "senha1234")
    response = client.post(
        f"/tarefas/fixar-tarefa/{tarefa.id}?filtro=pendentes&ordenar=data&direcao=asc",
        follow_redirects=False,
    )

    location = response.headers["Location"]
    assert "filtro=pendentes" in location
    assert "ordenar=data" in location
    assert "direcao=asc" in location


def test_excluir_tarefa_preserves_active_filter(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="concluido")

    login(client, "dono", "senha1234")
    response = client.post(
        f"/tarefas/excluir-tarefa/{tarefa.id}?filtro=concluidas",
        follow_redirects=False,
    )

    assert "filtro=concluidas" in response.headers["Location"]
    assert get_tarefas(dono.id) == []


def test_form_actions_carry_current_filters(client, make_user, make_tarefa):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/?filtro=pendentes&ordenar=data&direcao=asc")
    body = response.data.decode()

    assert f"/tarefas/alterar-status/{tarefa.id}?filtro=pendentes" in body
    assert f"/tarefas/excluir-tarefa/{tarefa.id}?filtro=pendentes" in body


def test_anonymous_cannot_mutate_tarefas(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    response = client.post(f"/tarefas/alterar-status/{tarefa.id}", follow_redirects=False)

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
    assert get_tarefas(dono.id)[0]["status"] == "pendente"
