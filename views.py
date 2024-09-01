from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView, UpdateView
from usuarios.forms import CadastroUsuarioChangeForm
from rolepermissions.mixins import HasRoleMixin
from django.urls import reverse
from usuarios.models import ProfessorModel, AlunoModel
from .forms import ProfessorUpdateForm, AlunoUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(TemplateView):
    template_name = 'index.html'


class MyProfileView(UpdateView):
    template_name = 'my_profile.html'
    form_class = CadastroUsuarioChangeForm

    def get_form_class(self):
        user = self.request.user

        # fazendo condicional para diferenciar os dois tipos de usuários do sistema;
        # em get_form_class estou apenas passando qual formulário deve ser retornado de acordo com user
        if user.is_ativo:
            if user.is_funcionario:
                return ProfessorUpdateForm
            return AlunoUpdateForm
        else:
            messages.error(self.request, 'Usuário não está ativo!')
            return CadastroUsuarioChangeForm
    
    def get_success_url(self):
        # get_success_url é para que eu redirecione corretamente meu usuário para seu formulário
        # pois agora temos dois rediirects possíveis (student / teacher)
        user = self.request.user 

        if user.is_funcionario:
            return reverse('teacher_form_update')
        return reverse('student_form_update')

    def get(self, request, *args, **kwargs):
        user = self.request.user
        user_form = CadastroUsuarioChangeForm(instance=user)

        # Eu preciso desta condicional para encontrar o profile que o User é uma instância;
        # No caso, foi mais trabalhoso construir esta view pois o meu profile recebe um User,
        # Então eu preciso fazer essa verificação para que eu encontre qual profile meu User está.
        if user.is_funcionario:
            teacher_profile = ProfessorModel.objects.get(usuario=user) # pegando o profile do User
            profile_form = ProfessorUpdateForm(instance=teacher_profile) # passando o user encontrado como instância do form
        else:
            student_profile = AlunoModel.objects.get(usuario=user)
            profile_form = AlunoUpdateForm(instnace=student_profile)

        # retornando os dois formulários (user, profile) como resposta
        return self.render_to_response(self.get_context_data(
            user_form=user_form,
            profile_form=profile_form
        ))

    def post(self, request, *args, **kwargs):
        user = self.request.user
        # Formulário do usuário especifico que está requisitando alteração dos dados pessoais
        user_form = CadastroUsuarioChangeForm(request.POST, instance=user) 

        # o POST é para que eu faça as alterações no meu banco de dados, 
        # é importante ter uma filtragem para que meu formulário esteja correto e limpo
        if user.is_funcionario:
            profile = ProfessorModel.objects.get(usuario=user) # encontrando perfil correto
            profile_form = ProfessorUpdateForm(request.POST, instance=profile) # passa o perfil encontrado como instância do formulário
        else:
            profile = AlunoModel.objects.get(usuario=user)
            profile_form = AlunoModel.objects.get(request.POST, instance=profile)
        
        # form_valid() para os dois formulários do usuário
        if user_form.is_valid() and profile_form.is_valid():
            # é preciso salvar o estado de ambos
            user_form.save() 
            profile_form.save()
            messages.success(request, 'Dados de usuário alterados com sucesso!')
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(
            user_form=user_form,
            profile_form=profile_form
        ))

    def get_object(self):
        # get_object é importante para o funcionamento da View (UpdateView)
        # isso porque eu passei aqui o que será meu argumento kwargs da url
        # no caso: <int:pk> nada mais será o valor de user.pk que faz o request.
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Dados alterados com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Ocorreu um erro! Tente novamente.')
        return self.render_to_response(self.get_context_data(form=form))