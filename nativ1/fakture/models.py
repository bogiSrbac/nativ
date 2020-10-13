from django.db import models
from django.db.models import F
from django.forms import ValidationError
from django.contrib.auth.models import User, AbstractBaseUser, BaseUserManager
import datetime
from django.utils import timezone
import decimal
from django.db.models.functions import ExtractYear, TruncYear


class MyKorisnikManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError('Morate unjeti email adresu')
        if not username:
            raise ValueError('Morate unjeti username')


        user = self.model(
            email=self.normalize_email(email),
            username=username,

        )
        user.set_password(password)
        user.save(using = self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Korisnik(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    ime = models.CharField(max_length=50)
    prezime = models.CharField(max_length=50)
    ime_oca = models.CharField(max_length=50)
    godina_rodjenja = models.DateField(blank=True, null=True)
    mjesto_rodjenja = models.CharField(max_length=50)
    mjesto_prebivalista = models.CharField(max_length=50)
    adresa = models.CharField(max_length=50)
    postanski_broj = models.CharField(max_length=50)
    telefon = models.CharField(max_length=50)
    naziv_preduzeca =  models.CharField(max_length=250, blank=True, null=True)
    adresa_preduzeca = models.CharField(max_length=250, blank=True, null=True)
    mjesto_preduzeca = models.CharField(max_length=250, blank=True, null=True)
    postanski_broj_preduzeca = models.CharField(max_length=250, blank=True, null=True)
    IBAN =  models.CharField(max_length=250, blank=True, null=True,default='BA395620998146211620')
    SWIFT_BIC = models.CharField(max_length=50, blank=True, null=True, default='RAZBBA22')
    telefon_mobilni = models.CharField(max_length=50, blank=True, null=True)
    fax = models.CharField(max_length=50, blank=True, null=True)
    zvanje = models.CharField(max_length=150, blank=True, null=True)
    pozicija = models.CharField(max_length=150, blank=True, null=True)
    email_preduzeca = models.EmailField(verbose_name="Email preduzeca", max_length=60, unique=True, blank=True, null=True)
    web_stranica = models.URLField(blank=True, null=True)
    banka_racun =  models.CharField(max_length=150, blank=True, null=True)

    profilna_slika = models.ImageField(upload_to='slike', blank=True, null=True)
    IZBOR_DRZAVE = (
        ('Bosna i Hercegovina', 'Bosna i Hercegovina'),
        ('Germany', 'Germany'),
        ('Poland', 'Poland')
    )
    drzava = models.CharField(max_length=50, choices=IZBOR_DRZAVE, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = MyKorisnikManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

class Kupac(models.Model):
    ime = models.CharField(max_length=50)
    prezime = models.CharField(max_length=50)
    naziv_firme = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    lokacija_grad = models.CharField(max_length=50)
    adresa_kupca = models.CharField(max_length=150)
    postanski_broj = models.CharField(max_length=50)
    IZBOR_DRZAVE = (
        ('Bosna i Hercegovina', 'Bosna i Hercegovina'),
        ('Germany', 'Germany'),
        ('Poland', 'Poland')
    )
    drzava = models.CharField(max_length=50, choices=IZBOR_DRZAVE, null=True, blank=True)

    def __str__(self):
        return self.naziv_firme

class Valute(models.Model):
    bam_evro = models.DecimalField(max_digits=8, decimal_places=6, default=1.955830, help_text='Unesite trenutni odnos BAM u odnosu na stranu valutu. <br>Maksimalan broj decimalnih mjeste je šest.')
    VALUTE = (
        ('EUR', 'EUR'),
        ('BAM', 'BAM'),
        ('USD', 'USD'),
        ('PLN', 'PLN'),
    )
    valute = models.CharField(max_length=10, choices=VALUTE, default='BAM')
    vrijednost_valute = models.DecimalField(max_digits=8, decimal_places=6, default=1.00)

    def __str__(self):
        return self.valute

    def save(self, *args, **kwargs):
        if self.valute == 'EUR':
            self.vrijednost_valute = 1 / self.bam_evro
        elif self.valute == 'PLN':
            self.vrijednost_valute = 1/ self.bam_evro
        elif self.valute == 'USD':
            self.vrijednost_valute = 1/ self.bam_evro
        super(Valute, self).save(*args, **kwargs)

class FaktureBrojevi(models.Model):
    broj_fakture = models.IntegerField(default=0)

    def __str__(self):
        return str(self.broj_fakture)


def get_new_default():
    if FaktureBrojevi.objects.filter(broj_fakture__isnull=True).order_by('broj_fakture').last():
        broj = FaktureBrojevi.objects.filter(broj_fakture__isnull=True).order_by('broj_fakture').last()
        broj.broj_fakture = 1
        broj_fakture = '000' + str(broj.broj_fakture)
        return broj_fakture
    else:
        if FaktureBrojevi.objects.filter(broj_fakture__isnull=False).order_by('broj_fakture').last():
            broj = FaktureBrojevi.objects.all().order_by('broj_fakture').last()
            if broj.broj_fakture <= 9:
                novi_broj = int(broj.broj_fakture) + 1
                broj_fakture = '000' + str(novi_broj)
                return broj_fakture
            elif 10 <= broj.broj_fakture <=99:
                novi_broj = broj.broj_fakture + 1
                broj_fakture = '00' + str(novi_broj)
                return broj_fakture
            elif 100 <= broj.broj_fakture <= 999:
                novi_broj = broj.broj_fakture + 1
                broj_fakture = '0' + str(novi_broj)
                return broj_fakture

class Faktura(models.Model):
    broj_fakture = models.CharField(max_length=50, default='0001', help_text='Polje se automatski ispunjava')
    kupac = models.ForeignKey(Kupac, on_delete=models.CASCADE, help_text='Izaberite kupca iz padajućeg menija')
    drzava = models.CharField(max_length=100, blank=True, null=True)
    datum_fakture = models.DateField(default=timezone.now, help_text='Izaberite datum iz datumara')
    rok_placanja = models.DateField(default=timezone.now, help_text='Polje se automatski ažurira', verbose_name='Rok plaćanja')
    INDETIFIKACIJSKI_BROJEVI = (
        ('210', '210'),
        ('220', '220'),
        ('230', '230'),
        ('240', '240'),
        ('300', '300'),
        ('400', '400'),
    )
    ident_brojevi = models.CharField(max_length=5, choices=INDETIFIKACIJSKI_BROJEVI, default='210', help_text='Izaberite identifikacijski broj iz padajućeg menija')
    REALIZACIJA = (
        ('P', 'Plaćeno'),
        ('NP', 'Nije plaćeno')
    )
    placeno = models.CharField(max_length=20, choices=REALIZACIJA, default='NP', verbose_name='Plaćeno', help_text='Izaberite opciju iz padajućeg menija')
    valuta = models.ForeignKey(Valute,  blank=True, default='BAM', on_delete=models.CASCADE)
    racun = models.CharField(max_length=20, default='RAČUN', blank=True, null=True)
    racun_njemacki = models.CharField(max_length=30, default='RECHNUNG', blank=True, null=True)
    avansno_uplaceno = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Devizno plaćanje upisati vrijednost u evrima', verbose_name='Avansno uplaćeno')
    nacin_placanja = models.CharField(max_length=100, blank=True, null=True, default='Žiro račun/Gotovinsko plaćanje')

    def clean(self, *args, **kwargs):
        if Faktura.objects.filter(broj_fakture__isnull=False):
            predzadnja_faktura_datum = Faktura.objects.all().order_by('-pk')[0]
            if self.datum_fakture < predzadnja_faktura_datum.datum_fakture:
                raise ValidationError('Datum kreirane fakture mora biti veći ili jednak od datuma prethodne fakture!')
        super(Faktura, self).clean(*args, **kwargs)

    def full_clean(self, *args, **kwargs):
        return self.clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        self.rok_placanja = self.datum_fakture + datetime.timedelta(days=30)
        self.kupac.save()
        d = Kupac.objects.get(pk=self.kupac.pk)
        self.drzava = d.drzava

        if d.drzava == 'Germany' or d.drzava == "Poland":
            self.valuta = Valute.objects.get(valute='EUR')
            self.racun = 'RAČUN'
            self.racun_njemacki = 'RECHNUNG'
            self.nacin_placanja = 'Devizno plaćanje'
        else:
            self.valuta = Valute.objects.get(valute='BAM')
            self.racun = 'RAČUN'
            self.racun_njemacki = ''
            self.nacin_placanja = 'Žiro račun/Gotovinsko plaćanje'
        if FaktureBrojevi.objects.filter(broj_fakture=0):
            k = FaktureBrojevi.objects.filter(broj_fakture=0)
            k.update(broj_fakture=F('broj_fakture')+1)
        else:
            k = FaktureBrojevi.objects.filter(broj_fakture__gte=1)
            k.update(broj_fakture=F('broj_fakture') - F('broj_fakture') + self.broj_fakture)
        super(Faktura, self).save(*args, **kwargs)
    class Meta:
        ordering = ['-pk']

    def __str__(self):
        return 'Broj fakture: ' + self.broj_fakture

class Pozicija(models.Model):
    naziv_pozicije = models.CharField(max_length=100, blank=True, null=True)
    pos_NSN = models.CharField(max_length=30, blank=True, null=True)
    pos_broj = models.IntegerField(blank=True, null=True, default=0)
    cijena = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    jedinica_mjere = models.CharField(max_length=50, default='kom')

    class Meta:
        ordering = ['naziv_pozicije']

    def __str__(self):
        return self.naziv_pozicije + ' ' + self.pos_NSN + ' ' + str(self.pos_broj)

class Usluga(models.Model):
    opis_usluge = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.opis_usluge



class Prodaja(models.Model):
    faktura = models.ForeignKey(Faktura, help_text='Polje se automatski ažurira', on_delete=models.CASCADE)
    pozicija = models.ForeignKey(Pozicija, help_text='Izaberi poziciju', on_delete=models.CASCADE)
    opis_usluge = models.ForeignKey(Usluga, blank=True, null=True, on_delete=models.CASCADE, help_text='Izaberi uslugu')
    kolicina = models.IntegerField(default=0, help_text='Unesi količinu', verbose_name='Količina')
    neto_cijena_proizvoda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    PDV = (
        ('0', '0'),
        ('17', '17')
    )
    pdv = models.CharField(max_length=10, choices=PDV, default='0')
    bruto_cijena_proizvoda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    neto_cijena = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bruto_cijena = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


    def __str__(self):
        return 'Broj fakture: ' + self.faktura.broj_fakture + ', ' + self.opis_usluge.opis_usluge

    def get_year(self):
        return self.faktura.datum_fakture.year



    def save(self, *args, **kwargs):

        d = Faktura.objects.get(id=self.faktura.pk)
        if d.drzava == 'Bosna i Hercegovina':
            self.pdv = '17'
            self.neto_cijena_proizvoda = self.pozicija.cijena
            self.neto_cijena = self.neto_cijena_proizvoda * self.kolicina
            super(Prodaja, self).save(*args, **kwargs)
        else:
            if d.drzava == 'Germany' or d.drzava == 'Poland':
                self.pdv = '0'
                self.neto_cijena_proizvoda = float(self.pozicija.cijena) * float(self.faktura.valuta.vrijednost_valute)
                self.neto_cijena_proizvoda = decimal.Decimal(round(self.neto_cijena_proizvoda, 2))
                self.neto_cijena = self.neto_cijena_proizvoda * self.kolicina
                super(Prodaja, self).save(*args, **kwargs)

        if self.pdv == '17':
            obracun = float(self.pozicija.cijena) * 0.17
            obracun2 = float(self.pozicija.cijena) + obracun
            obracun3 = obracun2 * self.kolicina
            self.bruto_cijena_proizvoda = decimal.Decimal(round(obracun2, 2))
            self.bruto_cijena = decimal.Decimal(round(obracun3, 2))
            super(Prodaja, self).save(*args, **kwargs)
        else:
            if self.pdv == '0':
                obracun = float(self.pozicija.cijena) * float(self.faktura.valuta.vrijednost_valute)
                #obracun1 = obracun * self.kolicina
                self.bruto_cijena_proizvoda = decimal.Decimal(round(obracun, 2))
                self.bruto_cijena =self.bruto_cijena_proizvoda * self.kolicina
                super(Prodaja, self).save(*args, **kwargs)


    class Meta:
        ordering = ['faktura']

class Ponuda(models.Model):
    broj_ponude = models.CharField(max_length=50, default='0001', help_text='Polje se automatski ispunjava')
    kupac = models.ForeignKey(Kupac, on_delete=models.CASCADE, help_text='Izaberite kupca iz padajućeg menija')
    drzava = models.CharField(max_length=100, blank=True, null=True)
    datum_ponude = models.DateField(default=timezone.now, help_text='Izaberite datum iz datumara')
    rok_placanja = models.DateField(default=timezone.now)
    INDETIFIKACIJSKI_BROJEVI = (
        ('210', '210'),
        ('220', '220'),
        ('230', '230'),
        ('240', '240'),
        ('300', '300'),
        ('400', '400'),
    )
    ident_brojevi = models.CharField(max_length=5, choices=INDETIFIKACIJSKI_BROJEVI, default='210', help_text='Izaberite identifikacijski broj iz padajućeg menija')
    REALIZACIJA = (
        ('P', 'Placeno'),
        ('NP', 'Nije placeno')
    )
    placeno = models.CharField(max_length=20, choices=REALIZACIJA, default='NP', verbose_name='Plaćeno', help_text='Izaberite opciju iz padajućeg menija')
    valuta = models.ForeignKey(Valute,  blank=True, default='BAM', on_delete=models.CASCADE)
    racun = models.CharField(max_length=20, default='RAČUN', blank=True, null=True)
    racun_njemacki = models.CharField(max_length=30, default='RECHNUNG', blank=True, null=True)
    avansno_uplaceno = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Devizno plaćanje upisati vrijednost u evrima', verbose_name='Avansno uplaćeno')
    nacin_placanja = models.CharField(max_length=100, blank=True, null=True, default='Žiro račun/Gotovinsko plaćanje')

    def clean(self, *args, **kwargs):
        if Ponuda.objects.filter(broj_ponude__isnull=False):
            predzadnja_ponuda_datum = Ponuda.objects.all().order_by('-pk')[0]
            if self.datum_ponude < predzadnja_ponuda_datum.datum_ponude:
                raise ValidationError('Datum kreirane ponude mora biti veći ili jednak od datuma prethodne ponude!')
        super(Ponuda, self).clean(*args, **kwargs)

    def full_clean(self, *args, **kwargs):
        return self.clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        self.rok_placanja = self.datum_ponude + datetime.timedelta(days=30)
        self.kupac.save()
        d = Kupac.objects.get(pk=self.kupac.pk)
        self.drzava = d.drzava
        if d.drzava == 'Germany' or d.drzava == "Poland":
            self.valuta = Valute.objects.get(valute='EUR')
            self.racun = 'RAČUN'
            self.racun_njemacki = 'RECHNUNG'
            self.nacin_placanja = 'Devizno plaćanje'
        else:
            self.valuta = Valute.objects.get(valute='BAM')
            self.racun = 'RAČUN'
            self.racun_njemacki = ''
            self.nacin_placanja = 'Žiro račun/Gotovinsko plaćanje'

        super(Ponuda, self).save(*args, **kwargs)
    class Meta:
        ordering = ['-pk']

    def __str__(self):
        return 'Broj ponude: ' + self.broj_ponude

class ProdajaPonuda(models.Model):
    ponuda = models.ForeignKey(Ponuda, help_text='Izaberi broj ponude', on_delete=models.CASCADE)
    pozicija = models.ForeignKey(Pozicija, help_text='Izaberi poziciju', on_delete=models.CASCADE)
    opis_usluge = models.ForeignKey(Usluga, blank=True, null=True, on_delete=models.CASCADE, help_text='Izaberi uslugu')
    kolicina = models.IntegerField(default=0, help_text='Unesi količinu', verbose_name='Količina')
    neto_cijena_proizvoda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    PDV = (
        ('0', '0'),
        ('17', '17')
    )
    pdv = models.CharField(max_length=10, choices=PDV, default='0')
    bruto_cijena_proizvoda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    neto_cijena = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bruto_cijena = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


    def __str__(self):
        return 'Broj fakture: ' + self.ponuda.broj_ponude + ', ' + self.opis_usluge.opis_usluge



    def save(self, *args, **kwargs):

        d = Ponuda.objects.get(id=self.ponuda.pk)
        if d.drzava == 'Bosna i Hercegovina':
            self.pdv = '17'
            self.neto_cijena_proizvoda = self.pozicija.cijena
            self.neto_cijena = self.neto_cijena_proizvoda * self.kolicina
            super(ProdajaPonuda, self).save(*args, **kwargs)
        else:
            if d.drzava == 'Germany' or d.drzava == 'Poland':
                self.pdv = '0'
                self.neto_cijena_proizvoda = float(self.pozicija.cijena) * float(self.ponuda.valuta.vrijednost_valute)
                self.neto_cijena_proizvoda = decimal.Decimal(round(self.neto_cijena_proizvoda, 2))
                self.neto_cijena = self.neto_cijena_proizvoda * self.kolicina
                super(ProdajaPonuda, self).save(*args, **kwargs)

        if self.pdv == '17':
            obracun = float(self.pozicija.cijena) * 0.17
            obracun2 = float(self.pozicija.cijena) + obracun
            obracun3 = obracun2 * self.kolicina
            self.bruto_cijena_proizvoda = decimal.Decimal(round(obracun2, 2))
            self.bruto_cijena = decimal.Decimal(round(obracun3, 2))
            super(ProdajaPonuda, self).save(*args, **kwargs)
        else:
            if self.pdv == '0':
                obracun = float(self.pozicija.cijena) * float(self.ponuda.valuta.vrijednost_valute)
                self.bruto_cijena_proizvoda = decimal.Decimal(round(obracun, 2))
                self.bruto_cijena =self.bruto_cijena_proizvoda * self.kolicina
                super(ProdajaPonuda, self).save(*args, **kwargs)

    class Meta:
        ordering = ['ponuda']





































