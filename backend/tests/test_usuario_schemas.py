"""Testes para validação de schemas de usuários."""

import pytest
from pydantic import ValidationError

from app.schemas.usuario import UsuarioAtualizar, UsuarioCriar


class TestUsuarioCriar:
    """Validação ao criar novo usuário."""

    def test_criar_usuario_valido(self):
        """Deve aceitar usuário com dados válidos."""
        usuario = UsuarioCriar(
            nome="João Silva",
            email="joao@example.com",
            senha="SecurePass123",
            admin=False,
        )
        assert usuario.nome == "João Silva"
        assert usuario.email == "joao@example.com"
        assert usuario.admin is False

    def test_email_normalizado_para_lowercase(self):
        """E-mail deve ser automaticamente convertido para minúsculas."""
        usuario = UsuarioCriar(
            nome="João Silva",
            email="JOAO@EXAMPLE.COM",
            senha="SecurePass123",
        )
        assert usuario.email == "joao@example.com"

    def test_rejeita_email_invalido(self):
        """Deve rejeitar email sem @."""
        with pytest.raises(ValidationError) as exc:
            UsuarioCriar(
                nome="João Silva",
                email="joao.example.com",
                senha="SecurePass123",
            )
        assert "email" in str(exc.value).lower()

    def test_rejeita_senha_curta(self):
        """Deve rejeitar senha com menos de 8 caracteres."""
        with pytest.raises(ValidationError) as exc:
            UsuarioCriar(
                nome="João Silva",
                email="joao@example.com",
                senha="Short1",
            )
        assert "senha" in str(exc.value).lower()

    def test_rejeita_senha_sem_maiuscula(self):
        """Deve rejeitar senha sem letra maiúscula."""
        with pytest.raises(ValidationError) as exc:
            UsuarioCriar(
                nome="João Silva",
                email="joao@example.com",
                senha="lowercase123",
            )
        assert "maiúscula" in str(exc.value).lower()

    def test_rejeita_senha_sem_minuscula(self):
        """Deve rejeitar senha sem letra minúscula."""
        with pytest.raises(ValidationError) as exc:
            UsuarioCriar(
                nome="João Silva",
                email="joao@example.com",
                senha="UPPERCASE123",
            )
        assert "minúscula" in str(exc.value).lower()

    def test_rejeita_senha_sem_digito(self):
        """Deve rejeitar senha sem dígito."""
        with pytest.raises(ValidationError) as exc:
            UsuarioCriar(
                nome="João Silva",
                email="joao@example.com",
                senha="NoDigitPass",
            )
        assert "dígito" in str(exc.value).lower()

    def test_rejeita_nome_vazio(self):
        """Deve rejeitar nome vazio."""
        with pytest.raises(ValidationError) as exc:
            UsuarioCriar(
                nome="",
                email="joao@example.com",
                senha="SecurePass123",
            )
        assert "nome" in str(exc.value).lower()

    def test_rejeita_campos_desconhecidos(self):
        """Deve rejeitar campos extras."""
        with pytest.raises(ValidationError) as exc:
            UsuarioCriar(
                nome="João Silva",
                email="joao@example.com",
                senha="SecurePass123",
                campo_extra="valor",  # type: ignore
            )
        assert "extra" in str(exc.value).lower()


class TestUsuarioAtualizar:
    """Validação ao atualizar usuário."""

    def test_atualizar_usuario_valido(self):
        """Deve aceitar atualização com dados válidos."""
        usuario = UsuarioAtualizar(
            nome="João Silva",
            senha="NewPassword123",
            ativo=True,
            versao=1,
        )
        assert usuario.nome == "João Silva"
        assert usuario.ativo is True

    def test_senha_opcional_em_atualizar(self):
        """Senha é opcional ao atualizar."""
        usuario = UsuarioAtualizar(
            nome="João Silva",
            ativo=True,
            versao=1,
        )
        assert usuario.senha is None

    def test_rejeita_senha_fraca_em_atualizar(self):
        """Deve validar força de senha se fornecida."""
        with pytest.raises(ValidationError) as exc:
            UsuarioAtualizar(
                nome="João Silva",
                senha="weak",
                ativo=True,
                versao=1,
            )
        assert "senha" in str(exc.value).lower()

    def test_versao_obrigatoria(self):
        """Campo versão é obrigatório para controle de concorrência."""
        with pytest.raises(ValidationError) as exc:
            UsuarioAtualizar(
                nome="João Silva",
                ativo=True,
            )  # type: ignore
        assert "versao" in str(exc.value).lower()
