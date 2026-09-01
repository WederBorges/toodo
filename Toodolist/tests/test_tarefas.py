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


def test_anonymous_cannot_mutate_tarefas(client, make_user, make_tarefa, get_tarefas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, status="pendente")

    response = client.post(f"/tarefas/alterar-status/{tarefa.id}", follow_redirects=False)

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
    assert get_tarefas(dono.id)[0]["status"] == "pendente"
