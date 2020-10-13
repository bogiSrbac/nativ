from django.shortcuts import render

# Create your views here.
import os
from django.conf import settings
import decimal
from weasyprint import HTML, CSS
from django.shortcuts import render
from django.views.generic import View, ListView, UpdateView, DetailView, CreateView, DeleteView
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from .models import Korisnik, Kupac, Usluga, Faktura, Prodaja, Pozicija, Valute, Ponuda, ProdajaPonuda
from django.template.loader import get_template, render_to_string
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from .forms import FakturaForma, ProdajaForma, PonudaForma, PonudaProdajaForma, FakturaUpdateForm
from django.db.models.functions import ExtractYear, TruncYear, Cast
from django.db.models.fields import DateField


def pdf_generator(request, pk):
    faktura = Faktura.objects.get(id=pk)
    prodaja = Prodaja.objects.filter(faktura__id=pk)
    prodaja_do_8 = Prodaja.objects.filter(faktura__id=pk)[:8]
    prodaja_8 = Prodaja.objects.filter(faktura__id=pk)[8:]
    prodaja_do_16 = Prodaja.objects.filter(faktura__id=pk)[8:24]
    prodaja_16 = Prodaja.objects.filter(faktura__id=pk)[24:]
    neto_suma = Prodaja.objects.filter(faktura__id=pk).aggregate(net_suma=Sum('neto_cijena'))
    bruto_suma = Prodaja.objects.filter(faktura__id=pk).aggregate(brt_suma=Sum('bruto_cijena'))
    formatirano1= round(neto_suma['net_suma'], 2)
    formatirano = round(bruto_suma['brt_suma'], 2)
    bruto_suma['brt_suma'] = formatirano
    neto_suma['net_suma'] = formatirano1
    prodaja_count = len(prodaja)
    korisnik = Korisnik.objects.get(username=request.user.username)
    valuta = Valute.objects.get(valute='EUR')
    avans = faktura.avansno_uplaceno
    bruto_suma_avans = bruto_suma['brt_suma'] - avans
    bruto_razlika = bruto_suma['brt_suma'] -  neto_suma['net_suma']


    context = {
        'korisnik': korisnik,
        'faktura': faktura,
        'prodaja': prodaja,
        'prodaja_5': prodaja[4:],
        'prodaja_24_40':prodaja[24:40],
        'prodaja_40_52':prodaja[40:52],
        'prodaja_8': prodaja_8,
        'prodaja_do_8': prodaja_do_8,
        'prodaja_do_16': prodaja_do_16,
        'prodaja_16': prodaja_16,
        'neto_suma': neto_suma,
        'bruto_suma': bruto_suma,
        'm': '1111',
        'prodaja_count': prodaja_count,
        'valuta':valuta,
        'avans': avans,
        'bruto_avans':bruto_suma_avans,
        'bruto_razlika': bruto_razlika
    }

    html_template = render_to_string('fakture/faktura_html.html', context)

    pdf_file = HTML(string=html_template,  base_url = request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="faktura broj {}.pdf"'.format(faktura.broj_fakture)
    return response




@login_required
#@permission_required
def pocetna_stranica(request):
    context = {}

    if Faktura.objects.filter(broj_fakture__isnull=True):
        pass
    else:
        fakture = Faktura.objects.filter(broj_fakture__isnull=False).order_by('-broj_fakture')
        #datum = Faktura.objects.values(Year=TruncYear('datum_fakture')).distinct()
        datum = Faktura.objects.dates('datum_fakture', 'year')
        valute = Valute.objects.all().order_by('valute')
        zadnja_faktura_datum = Faktura.objects.all().order_by('-pk').first()
        predzadnja_faktura_datum = Faktura.objects.all().order_by('-pk')[1]
        zadnja = zadnja_faktura_datum.datum_fakture
        predzadnja = predzadnja_faktura_datum.datum_fakture
        context = {
            'fakture':fakture,
            'datum':datum,
            'valute': valute,
            'zadnja_faktura_datum': zadnja,
            'pd':predzadnja,

        }

    return render(request, 'bazni_template.html', context)

def base(request):
    return render(request, 'fakture/base_nativ.html', {})

class KreirajValute(LoginRequiredMixin, CreateView):
    model = Valute
    fields = '__all__'
    template_name = 'fakture/valute_create.html'
    success_url = reverse_lazy('fakture:kreiraj-valutu')

    def get_context_data(self, *args, **kwargs):
        context = super(KreirajValute, self).get_context_data(**kwargs)
        context['valute'] = Valute.objects.all().order_by('valute')
        return context

class ValuteUpdate(LoginRequiredMixin, UpdateView):
    model = Valute
    fields = ('bam_evro',)
    template_name = 'fakture/valuta_update.html'

    def get_success_url(self):
        return reverse_lazy('fakture:index')

class FaktureLista(LoginRequiredMixin, ListView):
    model = Faktura
    template_name = 'fakture/faktura_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(FaktureLista, self).get_context_data(**kwargs)
        context['datum'] = Faktura.objects.dates('datum_fakture', 'year')
        return context

@login_required
def faktura_po_godinama(request, year):
    fakture = Faktura.objects.filter(datum_fakture__year=year)

    return render(request, 'fakture/godina_fakture.html', {'fakture':fakture})

class KreirajFakturu(LoginRequiredMixin, CreateView):
    model = Faktura
    form_class = FakturaForma
    template_name = 'fakture/faktura_create.html'
    success_url = reverse_lazy('fakture:faktura-prodaja')

    def get_initial(self):
        if not Faktura.objects.filter(broj_fakture__isnull=False).exists():
            faktura = '0001'
            return {'broj_fakture': faktura}
        else:
            broj = Faktura.objects.filter(broj_fakture__isnull=False).order_by('-pk')[0]
            faktura1 = int(broj.broj_fakture)
            if faktura1 <= 9:
                faktura = '000'+ str(faktura1+1)
                return {'broj_fakture': faktura}
            elif 10 <= faktura1 <= 99:
                faktura = '00' + str(faktura1+1)
                return {'broj_fakture': faktura}
            elif 100 <= faktura1 <= 999:
                faktura = '0'+str(faktura1+1)
                return {'broj_fakture': faktura}
    def get_context_data(self, **kwargs):
        context = super(KreirajFakturu, self).get_context_data(**kwargs)
        context['valute'] = Valute.objects.all()
        context['kupci'] = Kupac.objects.all()
        return context

    def get_success_url(self):
        return reverse('fakture:faktura-prodaja', args={self.object.pk})



class KreirajFakturuProdaja(LoginRequiredMixin, CreateView):
    form_class = ProdajaForma
    template_name = 'fakture/faktura_create_nastavak.html'
    success_url = reverse_lazy('fakture:faktura-prodaja')
    def get_initial(self, **kwargs):
        if Faktura.objects.filter(broj_fakture__isnull=True):
            faktura = '0001'
        else:
            broj = Faktura.objects.get(id=self.kwargs['pk'])
            faktura = broj
        return {'faktura':faktura}

    def get_context_data(self, **kwargs):
        context = super(KreirajFakturuProdaja, self).get_context_data(**kwargs)
        faktura = Faktura.objects.get(id=self.kwargs['pk'])
        neto_suma = Prodaja.objects.filter(faktura_id=faktura.pk).aggregate(net_suma=Sum('neto_cijena'))
        bruto_suma = Prodaja.objects.filter(faktura__id=faktura.pk).aggregate(brt_suma=Sum('bruto_cijena'))

        context['faktura']= Faktura.objects.get(id=self.kwargs['pk'])
        context['prodaja'] = Prodaja.objects.all().filter(faktura__id=faktura.pk)
        context['neto_suma'] = neto_suma
        context['bruto_suma'] = bruto_suma
        context['pozicije'] = Pozicija.objects.all()
        context['usluge'] = Usluga.objects.all()
        return context
    def get_success_url(self):
        return reverse('fakture:faktura-prodaja', kwargs={'pk':self.object.faktura.pk})

class ProdajaDetalji(LoginRequiredMixin, DetailView):
    model = Prodaja
    template_name = 'fakture/prodaja_detail.html'
    def get_success_url(self):
        return reverse('fakture:faktura-prodaja', args={self.object.pk})

class ProdajaIzmjena(LoginRequiredMixin, UpdateView):
    model = Prodaja
    fields = '__all__'
    template_name = 'fakture/update_prodaja.html'
    def get_success_url(self):
        return reverse('fakture:faktura-prodaja', kwargs={'pk':self.object.faktura.pk})

class FakturaUpdate(LoginRequiredMixin, UpdateView):
    model = Faktura
    form_class = FakturaUpdateForm
    template_name = 'fakture/faktura_update.html'
    success_url = reverse_lazy('fakture:faktura-prodaja-izmjena')

    def get_success_url(self):
        return reverse('fakture:faktura-prodaja', args={self.object.pk})

class ProdajaGlavnaUpdate(LoginRequiredMixin, UpdateView):
    model = Prodaja
    form_class = ProdajaForma
    template_name = 'fakture/prodaja_glavna_update.html'
    success_url = reverse_lazy('fakture:faktura-prodaja-izmjena')


    def get_context_data(self, **kwargs):
        context = super(ProdajaGlavnaUpdate, self).get_context_data(**kwargs)
        faktura = Faktura.objects.get(id=self.kwargs['pk'])
        neto_suma = Prodaja.objects.filter(faktura__broj_fakture=faktura.broj_fakture).aggregate(
            net_suma=Sum('neto_cijena'))
        bruto_suma = Prodaja.objects.filter(faktura__broj_fakture=faktura.broj_fakture).aggregate(
            brt_suma=Sum('bruto_cijena'))

        context['faktura'] = Faktura.objects.get(id=self.kwargs['pk'])
        context['prodaja'] = Prodaja.objects.all().filter(faktura__broj_fakture=faktura.broj_fakture)
        context['neto_suma'] = neto_suma
        context['bruto_suma'] = bruto_suma
        return context

    def get_success_url(self):
        return reverse('fakture:faktura-prodaja-izmjena', kwargs={'pk': self.object.faktura.pk})



def faktura_skica_gotova(request, pk):
    faktura = Faktura.objects.get(id=pk)
    prodaja = Prodaja.objects.filter(faktura_id=pk)
    prodaja_do_8 = Prodaja.objects.filter(faktura_id=pk)[:8]
    prodaja_8 = Prodaja.objects.filter(faktura_id=pk)[8:]
    prodaja_do_16 = Prodaja.objects.filter(faktura_id=pk)[8:24]
    prodaja_16 = Prodaja.objects.filter(faktura_id=pk)[24:]
    neto_suma = Prodaja.objects.filter(faktura_id=pk).aggregate(net_suma=Sum('neto_cijena'))
    bruto_suma = Prodaja.objects.filter(faktura_id=pk).aggregate(brt_suma=Sum('bruto_cijena'))
    formatirano1= round(neto_suma['net_suma'], 2)
    formatirano = round(bruto_suma['brt_suma'], 2)
    bruto_suma['brt_suma'] = formatirano
    neto_suma['net_suma'] = formatirano1
    prodaja_count = len(prodaja)
    korisnik = Korisnik.objects.get(username=request.user.username)
    valuta = Valute.objects.get(valute='EUR')
    avans = faktura.avansno_uplaceno
    bruto_suma_avans = bruto_suma['brt_suma'] - avans
    bruto_razlika = bruto_suma['brt_suma'] - neto_suma['net_suma']

    context = {
        'korisnik': korisnik,
        'faktura': faktura,
        'prodaja': prodaja,
        'prodaja_5': prodaja[4:],
        'prodaja_24_40':prodaja[24:40],
        'prodaja_40_52':prodaja[40:52],
        'prodaja_8': prodaja_8,
        'prodaja_do_8': prodaja_do_8,
        'prodaja_do_16': prodaja_do_16,
        'prodaja_16': prodaja_16,
        'neto_suma': neto_suma,
        'bruto_suma': bruto_suma,
        'm': '1111',
        'prodaja_count': prodaja_count,
        'valuta':valuta,
        'avans': avans,
        'bruto_avans':bruto_suma_avans,
        'bruto_razlika': bruto_razlika
    }


    return render(request, 'fakture/faktura_skica_gotovo.html', context)

class ProdajaBrisanje(LoginRequiredMixin, DeleteView):
    model = Prodaja
    success_url = reverse_lazy('fakture:faktura-prodaja')
    template_name = 'fakture/prodaja_delete.html'

    def get_success_url(self):
        return reverse('fakture:faktura-prodaja', kwargs={'pk': self.object.faktura.pk})

class KupciLista(LoginRequiredMixin, ListView):
    model = Kupac
    template_name = 'fakture/kupac_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(KupciLista, self).get_context_data(**kwargs)
        context['zemlja'] = Kupac.objects.values('drzava').order_by('drzava').distinct()
        return context

class KupacNovi(LoginRequiredMixin, CreateView):
    model = Kupac
    fields = '__all__'
    template_name = 'fakture/kupac_create.html'
    success_url = reverse_lazy('fakture:lista-kupci')

class KupacUpdate(LoginRequiredMixin, UpdateView):
    model = Kupac
    fields = '__all__'
    template_name = 'fakture/kupac_izmjeni.html'
    success_url = reverse_lazy('fakture:kupac-update')

class KupacDetalji(LoginRequiredMixin, DetailView):
    model = Kupac
    template_name = 'fakture/kupac_detalji.html'

class UslugeList(LoginRequiredMixin, ListView):
    model = Usluga
    template_name = 'fakture/usluge_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(UslugeList, self).get_context_data(**kwargs)
        context['pozicije'] = Pozicija.objects.all().order_by('naziv_pozicije')
        return context

class UslugaKreiraj(LoginRequiredMixin, CreateView):
    model = Usluga
    fields = '__all__'
    template_name = 'fakture/usluga_create.html'
    success_url = reverse_lazy('fakture:usluge-lista')

class UslugaUpdate(LoginRequiredMixin, UpdateView):
    model = Usluga
    fields = '__all__'
    template_name = 'fakture/usluge_update.html'
    success_url = reverse_lazy('fakture:usluge-lista')

class PozicijaKreiraj(LoginRequiredMixin, CreateView):
    model = Pozicija
    fields = '__all__'
    template_name = 'fakture/pozicija_kreiraj.html'
    success_url = reverse_lazy('fakture:usluge-lista')

class PozicijaUpdate(LoginRequiredMixin, UpdateView):
    model = Pozicija
    fields = '__all__'
    template_name = 'fakture/pozicije_update.html'
    success_url = reverse_lazy('fakture:usluge-lista')

class PonudaLista(LoginRequiredMixin, ListView):
    model = Ponuda
    template_name = 'fakture/ponuda_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PonudaLista, self).get_context_data(**kwargs)
        context['datum'] = Ponuda.objects.dates('datum_ponude', 'year')
        return context

class KreirajPonudu(LoginRequiredMixin, CreateView):
    model = Ponuda
    form_class = PonudaForma
    template_name = 'fakture/ponuda_create.html'
    success_url = reverse_lazy('fakture:ponuda-prodaja')

    def get_initial(self):
        if not Ponuda.objects.filter(broj_ponude__isnull=False).exists():
            faktura = '0001'
            return {'broj_ponude': faktura}
        else:
            broj = Ponuda.objects.filter(broj_ponude__isnull=False).order_by('-pk')[0]
            faktura1 = int(broj.broj_ponude)
            if faktura1 <= 9:
                faktura = '000'+ str(faktura1+1)
                return {'broj_ponude': faktura}
            elif 10 <= faktura1 <= 99:
                faktura = '00' + str(faktura1+1)
                return {'broj_ponude': faktura}
            elif 100 <= faktura1 <= 999:
                faktura = '0'+str(faktura1+1)
                return {'broj_ponude': faktura}
    def get_context_data(self, **kwargs):
        context = super(KreirajPonudu, self).get_context_data(**kwargs)
        context['valute'] = Valute.objects.all()
        context['kupci'] = Kupac.objects.all()
        return context

    def get_success_url(self):
        return reverse('fakture:ponuda-prodaja', args={self.object.pk})

class KreirajPonuduProdaja(LoginRequiredMixin, CreateView):
    form_class = PonudaProdajaForma
    template_name = 'fakture/ponuda_create_nastavak.html'
    success_url = reverse_lazy('fakture:ponuda-prodaja')
    def get_initial(self, **kwargs):
        if Ponuda.objects.filter(broj_ponude__isnull=True):
            faktura = '0001'
        else:
            broj = Ponuda.objects.get(id=self.kwargs['pk'])
            faktura = broj
        return {'ponuda':faktura}

    def get_context_data(self, **kwargs):
        context = super(KreirajPonuduProdaja, self).get_context_data(**kwargs)
        ponuda = Ponuda.objects.get(id=self.kwargs['pk'])
        neto_suma = ProdajaPonuda.objects.filter(ponuda_id=ponuda.pk).aggregate(net_suma=Sum('neto_cijena'))
        bruto_suma = ProdajaPonuda.objects.filter(ponuda_id=ponuda.pk).aggregate(brt_suma=Sum('bruto_cijena'))

        context['ponuda']= Ponuda.objects.get(id=self.kwargs['pk'])
        context['prodaja'] = ProdajaPonuda.objects.all().filter(ponuda_id=ponuda.pk)
        context['neto_suma'] = neto_suma
        context['bruto_suma'] = bruto_suma
        context['pozicije'] = Pozicija.objects.all()
        context['usluge'] = Usluga.objects.all()
        return context
    def get_success_url(self):
        return reverse('fakture:ponuda-prodaja', kwargs={'pk':self.object.ponuda.pk})

class ProdajaPonudaDetalji(LoginRequiredMixin, DetailView):
    model = ProdajaPonuda
    template_name = 'fakture/ponuda_prodaja_detail.html'
    def get_success_url(self):
        return reverse('fakture:ponuda-prodaja', args={self.object.pk})

def ponuda_skica_gotova(request, pk):
    ponuda = Ponuda.objects.get(id=pk)
    prodaja = ProdajaPonuda.objects.filter(ponuda_id=pk)
    prodaja_do_8 = ProdajaPonuda.objects.filter(ponuda_id=pk)[:8]
    prodaja_8 = ProdajaPonuda.objects.filter(ponuda_id=pk)[8:]
    prodaja_do_16 = ProdajaPonuda.objects.filter(ponuda_id=pk)[8:24]
    prodaja_16 = ProdajaPonuda.objects.filter(ponuda_id=pk)[24:]
    neto_suma = ProdajaPonuda.objects.filter(ponuda_id=pk).aggregate(net_suma=Sum('neto_cijena'))
    bruto_suma = ProdajaPonuda.objects.filter(ponuda_id=pk).aggregate(brt_suma=Sum('bruto_cijena'))
    formatirano1= round(neto_suma['net_suma'], 2)
    formatirano = round(bruto_suma['brt_suma'], 2)
    bruto_suma['brt_suma'] = formatirano
    neto_suma['net_suma'] = formatirano1
    prodaja_count = len(prodaja)
    korisnik = Korisnik.objects.get(username=request.user.username)
    valuta = Valute.objects.get(valute='EUR')
    avans = ponuda.avansno_uplaceno
    bruto_suma_avans = bruto_suma['brt_suma'] - avans
    bruto_razlika = bruto_suma['brt_suma'] - neto_suma['net_suma']

    context = {
        'korisnik': korisnik,
        'ponuda': ponuda,
        'prodaja': prodaja,
        'prodaja_5': prodaja[4:],
        'prodaja_24_40':prodaja[24:40],
        'prodaja_40_52':prodaja[40:52],
        'prodaja_8': prodaja_8,
        'prodaja_do_8': prodaja_do_8,
        'prodaja_do_16': prodaja_do_16,
        'prodaja_16': prodaja_16,
        'neto_suma': neto_suma,
        'bruto_suma': bruto_suma,
        'm': '1111',
        'prodaja_count': prodaja_count,
        'valuta':valuta,
        'avans': avans,
        'bruto_avans':bruto_suma_avans,
        'bruto_razlika': bruto_razlika
    }


    return render(request, 'fakture/ponuda_skica_gotovo.html', context)

def pdf_generator_ponuda(request, pk):
    ponuda = Ponuda.objects.get(id=pk)
    prodaja = ProdajaPonuda.objects.filter(ponuda_id=pk)
    prodaja_do_8 = ProdajaPonuda.objects.filter(ponuda_id=pk)[:8]
    prodaja_8 = ProdajaPonuda.objects.filter(ponuda_id=pk)[8:]
    prodaja_do_16 = ProdajaPonuda.objects.filter(ponuda_id=pk)[8:24]
    prodaja_16 = ProdajaPonuda.objects.filter(ponuda_id=pk)[24:]
    neto_suma = ProdajaPonuda.objects.filter(ponuda_id=pk).aggregate(net_suma=Sum('neto_cijena'))
    bruto_suma = ProdajaPonuda.objects.filter(ponuda_id=pk).aggregate(brt_suma=Sum('bruto_cijena'))
    formatirano1 = round(neto_suma['net_suma'], 2)
    formatirano = round(bruto_suma['brt_suma'], 2)
    bruto_suma['brt_suma'] = formatirano
    neto_suma['net_suma'] = formatirano1
    prodaja_count = len(prodaja)
    korisnik = Korisnik.objects.get(username=request.user.username)
    valuta = Valute.objects.get(valute='EUR')
    avans = ponuda.avansno_uplaceno
    bruto_suma_avans = bruto_suma['brt_suma'] - avans
    bruto_razlika = bruto_suma['brt_suma'] - neto_suma['net_suma']

    context = {
        'korisnik': korisnik,
        'ponuda': ponuda,
        'prodaja': prodaja,
        'prodaja_5': prodaja[4:],
        'prodaja_24_40': prodaja[24:40],
        'prodaja_40_52': prodaja[40:52],
        'prodaja_8': prodaja_8,
        'prodaja_do_8': prodaja_do_8,
        'prodaja_do_16': prodaja_do_16,
        'prodaja_16': prodaja_16,
        'neto_suma': neto_suma,
        'bruto_suma': bruto_suma,
        'm': '1111',
        'prodaja_count': prodaja_count,
        'valuta': valuta,
        'avans': avans,
        'bruto_avans': bruto_suma_avans,
        'bruto_razlika': bruto_razlika,
    }



    html_template = render_to_string('fakture/ponuda_pdf.html', context)

    pdf_file = HTML(string=html_template,  base_url = request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="ponuda broj {}.pdf"'.format(ponuda.broj_ponude)
    return response

class PonudaUpdate(LoginRequiredMixin, UpdateView):
    model = Ponuda
    fields = '__all__'
    template_name = 'fakture/ponuda_update.html'


    def get_success_url(self):
        return reverse('fakture:ponuda-prodaja', args={self.object.pk})

class PonudaProdajaBrisanje(LoginRequiredMixin, DeleteView):
    model = ProdajaPonuda
    success_url = reverse_lazy('fakture:ponuda-prodaja')
    template_name = 'fakture/prodaja-delite.html'

    def get_success_url(self):
        return reverse('fakture:ponuda-prodaja', kwargs={'pk': self.object.pk})


class PonudaProdajaIzmjena(LoginRequiredMixin, UpdateView):
    model = ProdajaPonuda
    fields = '__all__'
    template_name = 'fakture/ponuda-prodaja-izmjena.html'

    def get_success_url(self):
        return reverse('fakture:ponuda-prodaja', kwargs={'pk':self.object.ponuda.pk})

@login_required
def ponude_po_godinama(request, year):
    ponuda = Ponuda.objects.filter(datum_ponude__year=year)

    return render(request, 'fakture/ponuda_godine.html', {'ponuda':ponuda})

