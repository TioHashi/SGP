from django import forms

from .models import Escola, Frequencia, Servidor


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
            'ativo',
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_saida': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'formacao': 'Formação',
            'instituicao': 'Instituição',
            'funcao': 'Função',
            'carga_horaria': 'Carga horária',
            'data_admissao': 'Data de admissão',
            'data_inicio': 'Data de início',
            'data_saida': 'Data de saída',
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


class FolhaFiltroForm(forms.Form):
    mes = forms.ChoiceField(choices=Frequencia.MESES_CHOICES)
    ano = forms.ChoiceField(choices=Frequencia.ANO_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'field-control')


class TransferirServidorForm(forms.Form):
    escola_destino = forms.ModelChoiceField(
        queryset=Escola.objects.filter(ativa=True),
        label='Escola de destino',
    )

    def __init__(self, *args, servidor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if servidor:
            self.fields['escola_destino'].queryset = Escola.objects.filter(ativa=True).exclude(pk=servidor.escola_id)
        self.fields['escola_destino'].widget.attrs.setdefault('class', 'field-control')
