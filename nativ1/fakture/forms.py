from django.forms import ModelForm
from django import forms
from django.db.models.functions import Concat
from .models import Faktura, Prodaja, Ponuda, ProdajaPonuda
from django.contrib.admin import widgets
from django.core.exceptions import ValidationError


class FakturaForma(ModelForm):
    class Meta:
        model = Faktura
        fields = '__all__'
        exclude = ('drzava','rok_placanja', 'valuta', 'racun', 'racun_njemacki', 'nacin_placanja')
        widgets = {
            'datum_fakture': forms.DateInput(format=('%d/%m/%Y'), attrs={'class':'form-control', 'placeholder':'Select a date', 'type':'date'}),
        }

    def clean(self):
        broj_f = self.cleaned_data['broj_fakture']
        datum_f = self.cleaned_data['datum_fakture']
        datum = Faktura.objects.filter(broj_fakture=broj_f, datum_fakture__year=datum_f.year)
        if datum:
            raise ValidationError('Ne možete unjeti isti broj fakture u tekućoj godini!')

class FakturaUpdateForm(ModelForm):

    class Meta:
        model = Faktura
        exclude = ('drzava','rok_placanja', 'valuta', 'racun', 'racun_njemacki', 'nacin_placanja')

class ProdajaForma(ModelForm):

    class Meta:
        model = Prodaja
        fields = '__all__'
        exclude = ('neto_cijena_proizvoda', 'pdv', 'bruto_cijena_proizvoda', 'neto_cijena', 'bruto_cijena')

    def clean(self):
        faktura_id = self.cleaned_data['faktura']
        poz_np = self.cleaned_data['pozicija']
        opi_usl = self.cleaned_data['opis_usluge']

        usluga = Prodaja.objects.filter(faktura_id=faktura_id.pk, pozicija__naziv_pozicije=poz_np.naziv_pozicije,
                                        pozicija__pos_NSN=poz_np.pos_NSN, pozicija__pos_broj=poz_np.pos_broj,
                                        opis_usluge=opi_usl.pk)

        if usluga:
            raise ValidationError('Pokušavate unjeti već postojeće elemente!')

class PonudaForma(ModelForm):
    class Meta:
        model = Ponuda
        fields = '__all__'
        exclude = ('drzava','rok_placanja', 'valuta', 'racun', 'racun_njemacki', 'nacin_placanja')
        widgets = {
            'datum_ponude': forms.DateInput(format=('%d/%m/%Y'), attrs={'class':'form-control', 'placeholder':'Select a date', 'type':'date'}),
        }

    def clean(self):
        broj_p = self.cleaned_data['broj_ponude']
        datum_p = self.cleaned_data['datum_ponude']
        datum = Ponuda.objects.filter(broj_ponude=broj_p, datum_ponude__year=datum_p.year)
        if datum:
            raise ValidationError('Ne možete unjeti isti broj ponude u tekućoj godini!')

class PonudaProdajaForma(ModelForm):

    class Meta:
        model = ProdajaPonuda
        fields = '__all__'
        exclude = ('neto_cijena_proizvoda', 'pdv', 'bruto_cijena_proizvoda', 'neto_cijena', 'bruto_cijena')

    def clean(self):
        ponuda_id = self.cleaned_data['ponuda']
        poz_np = self.cleaned_data['pozicija']
        opi_usl = self.cleaned_data['opis_usluge']

        usluga = ProdajaPonuda.objects.filter(ponuda_id=ponuda_id.pk, pozicija__naziv_pozicije=poz_np.naziv_pozicije,
                                        pozicija__pos_NSN=poz_np.pos_NSN, pozicija__pos_broj=poz_np.pos_broj,
                                        opis_usluge=opi_usl.pk)

        if usluga:
            raise ValidationError('Pokušavate unjeti već postojeće elemente!')