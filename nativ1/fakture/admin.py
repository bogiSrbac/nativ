from django.contrib import admin
from .models import Korisnik, Kupac, Prodaja, Faktura, Usluga, Pozicija, Valute, FaktureBrojevi, Ponuda, ProdajaPonuda


class ProdajaInline(admin.TabularInline):
    model = Prodaja

class FaktureAdmin(admin.ModelAdmin):
   list_display = ('broj_fakture', 'kupac', 'datum_fakture', 'rok_placanja', 'placeno', 'valuta', 'avansno_uplaceno', 'nacin_placanja')
   fields = ['broj_fakture', 'kupac', ('datum_fakture', 'rok_placanja', 'placeno', 'valuta', 'avansno_uplaceno', 'nacin_placanja')]
   inlines = [ProdajaInline]



admin.site.register(Korisnik)
admin.site.register(Kupac)
admin.site.register(Prodaja)
admin.site.register(Faktura, FaktureAdmin)
admin.site.register(Usluga)
admin.site.register(Pozicija)
admin.site.register(Valute)
admin.site.register(FaktureBrojevi)
admin.site.register(Ponuda)
admin.site.register(ProdajaPonuda)
