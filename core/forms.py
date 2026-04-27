from django import forms

from .models import Servidor


class ServidorForm(forms.ModelForm):
    class Meta:
        model = Servidor
        fields = [
            'escola',
            'nome',
            'sexo',
            'rg',
            'cpf',
            'data_nascimento',
            'telefone',
            'email',
            'logradouro',
            'numero',
            'zona',
            'bairro',
            'estado',
            'municipio',
            'cep',
            'escolaridade',
            'formacao',
            'instituicao',
            'funcao',
            'cargo',
            'vinculo',
            'carga_horaria',
            'data_admissao',
            'data_inicio',
            'data_saida',
            'banco',
            'agencia',
            'conta',
            'ativo',
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_saida': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'field-control')

        if user and not user.is_superuser:
            self.fields.pop('escola')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and not self.user.is_superuser:
            perfil = getattr(self.user, 'perfilusuario', None)
            if perfil and perfil.escola:
                instance.escola = perfil.escola
        if commit:
            instance.save()
            self.save_m2m()
        return instance
