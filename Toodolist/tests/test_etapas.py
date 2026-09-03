from tests.conftest import login


def test_adicionar_etapa_creates_step(client, make_user, make_tarefa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id)

    login(client, "dono", "senha1234")
    response = client.post(
        f"/tarefas/adicionar-etapa/{tarefa.id}",
        data={"descricao": "Ligar para o fornecedor"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert f"open_etapas={tarefa.id}" in response.headers["Location"]

    etapas = get_etapas(tarefa.id)
    assert len(etapas) == 1
    assert etapas[0]["descricao"] == "Ligar para o fornecedor"
    assert etapas[0]["concluida"] is False


def test_adicionar_etapa_ignores_blank_description(client, make_user, make_tarefa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id)

    login(client, "dono", "senha1234")
    client.post(f"/tarefas/adicionar-etapa/{tarefa.id}", data={"descricao": "   "})

    assert get_etapas(tarefa.id) == []


def test_cannot_add_etapa_to_another_users_tarefa(client, make_user, make_tarefa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    atacante = make_user(nome="atacante", senha="senha1234")
    tarefa = make_tarefa(dono.id)

    login(client, "atacante", "senha1234")
    response = client.post(
        f"/tarefas/adicionar-etapa/{tarefa.id}",
        data={"descricao": "Etapa maliciosa"},
        follow_redirects=True,
    )

    assert b"Tarefa inexistente" in response.data
    assert get_etapas(tarefa.id) == []


def test_alternar_etapa_toggles_concluida(client, make_user, make_tarefa, make_etapa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id)
    etapa = make_etapa(tarefa.id, descricao="Passo 1")

    login(client, "dono", "senha1234")
    client.post(f"/tarefas/alternar-etapa/{etapa.id}")
    assert get_etapas(tarefa.id)[0]["concluida"] is True

    client.post(f"/tarefas/alternar-etapa/{etapa.id}")
    assert get_etapas(tarefa.id)[0]["concluida"] is False


def test_cannot_alternar_etapa_of_another_users_tarefa(client, make_user, make_tarefa, make_etapa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    atacante = make_user(nome="atacante", senha="senha1234")
    tarefa = make_tarefa(dono.id)
    etapa = make_etapa(tarefa.id, descricao="Passo 1")

    login(client, "atacante", "senha1234")
    response = client.post(f"/tarefas/alternar-etapa/{etapa.id}", follow_redirects=True)

    assert b"Etapa inexistente" in response.data
    assert get_etapas(tarefa.id)[0]["concluida"] is False


def test_excluir_etapa_removes_it(client, make_user, make_tarefa, make_etapa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id)
    etapa = make_etapa(tarefa.id)

    login(client, "dono", "senha1234")
    client.post(f"/tarefas/excluir-etapa/{etapa.id}")

    assert get_etapas(tarefa.id) == []


def test_cannot_excluir_etapa_of_another_users_tarefa(client, make_user, make_tarefa, make_etapa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    atacante = make_user(nome="atacante", senha="senha1234")
    tarefa = make_tarefa(dono.id)
    etapa = make_etapa(tarefa.id)

    login(client, "atacante", "senha1234")
    response = client.post(f"/tarefas/excluir-etapa/{etapa.id}", follow_redirects=True)

    assert b"Etapa inexistente" in response.data
    assert len(get_etapas(tarefa.id)) == 1


def test_anonymous_cannot_mutate_etapas(client, make_user, make_tarefa, make_etapa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id)
    etapa = make_etapa(tarefa.id)

    response = client.post(f"/tarefas/alternar-etapa/{etapa.id}", follow_redirects=False)

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
    assert get_etapas(tarefa.id)[0]["concluida"] is False


def test_excluir_tarefa_cascades_etapas(client, make_user, make_tarefa, make_etapa, get_etapas):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id)
    make_etapa(tarefa.id)

    login(client, "dono", "senha1234")
    client.post(f"/tarefas/excluir-tarefa/{tarefa.id}")

    assert get_etapas(tarefa.id) == []


def test_home_shows_etapas_progress(client, make_user, make_tarefa, make_etapa):
    dono = make_user(nome="dono", senha="senha1234")
    tarefa = make_tarefa(dono.id, tarefa="Organizar mudança")
    make_etapa(tarefa.id, descricao="Passo 1", concluida=True)
    make_etapa(tarefa.id, descricao="Passo 2", concluida=False)

    login(client, "dono", "senha1234")
    response = client.get("/tarefas/")

    assert "1/2 etapas".encode() in response.data
    assert "Passo 1".encode() in response.data
    assert "Passo 2".encode() in response.data
