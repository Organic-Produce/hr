# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import CharField
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.contrib.auth.models import User, UserManager
from django.utils.timezone import now
from django.utils.translation import (ugettext, ugettext_lazy as _,
                                      pgettext_lazy as __)
from mezzanine.pages.models import Page
from cartridge.shop import fields 
from cartridge.shop.models import ProductVariation, Product, Cart
from datetime import timedelta

class Venta(Cart):
    class Meta:
        app_label = "shop"
        proxy = True    
        
    def otro_item(self, ProductVariation, cantidad=1):
        self.add_item(ProductVariation, cantidad)

class Zapato(Product):
    codigo = models.CharField(max_length=6)
    marcas = models.ForeignKey("Marca", blank=True, verbose_name=_("Marca del producto"))
    stock_min = models.IntegerField("Cantidad minima de artículos", default=10)
    codigo_proveedor = CharField(max_length=50, blank=True, null=True)
    color_original = CharField(max_length=50, blank=True, null=True)

    @property
    def stock(self) :
        return sum([va.num_in_stock for va in self.variations.all() if va.num_in_stock is not None])
        #sum_of_all_numbers= reduce(lambda q,p: p+q, list)

    class Meta:
        app_label = "shop"
        verbose_name = "Producto"

    def __repr__(self):
        return self.codigo # self.marcas.codigo + self.codigo.zfill(5)

class Pedido(models.Model):
    producto = models.ForeignKey("Zapato")
    date_captured = models.DateTimeField(_("Fecha"), auto_now_add=True, null=True)
    terminado = models.BooleanField(default=False)

    class Meta:
        app_label="shop"

class Surtido(Pedido):
    factura = models.ForeignKey("Factura")

    class Meta:
        app_label="shop"

class InstanceVariation(models.Model):
    zapato_variation = models.ForeignKey(ProductVariation)
    cantidad = models.IntegerField(default=0)
    date_captured = models.DateTimeField(_("Fecha"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = "shop"

class MoreProductVariation(InstanceVariation):
    surtido = models.ForeignKey("Surtido", null=True)
    costo = fields.MoneyField(blank=True, null=True,)# default=self.zapato_variation.unit_price)

    class Meta:
        app_label="shop"

class PedidoVariation(InstanceVariation):
    surtido = models.ForeignKey("Pedido", null=True)

    class Meta:
        app_label="shop"

class VentaVariation(InstanceVariation):
    surtido = models.ForeignKey("MovimientoCaja", null=True)
    precio_unitario = fields.MoneyField(blank=True, null=True,)# default=self.zapato_variation.unit_price)

    class Meta:
        app_label="shop"

class PageManager(models.Manager):
    def get_queryset(self):
        return super(PageManager, self).get_queryset().order_by('title')

class Proveedor(Page):
    marcas = models.ManyToManyField("Marca", verbose_name=_("Marcas"))
    telefono = CharField(max_length=100, blank=True, null=True)
    direccion = CharField(_("Dirección postal"), max_length=300, blank=True, null=True)
    correo = models.EmailField(_("Correo electrónico"), blank=True, null=True)
    url = models.URLField(_("Página WEB"), blank=True, null=True)
    contacto = models.ForeignKey("Cliente", blank=True, null=True, related_name="user_empresa", limit_choices_to = {'groups__name__in': ['Proveedor']})
    rfc = CharField(_("Registro Federal de Causantes"), max_length=20, blank=True, null=True)
    
    objects = PageManager()

    class Meta:
        app_label="shop"
        verbose_name_plural = _("Proveedores")

class Marca(Page):
    codigo = CharField(_("Abreviación"), max_length=5,unique=True)
    cargo = fields.PercentageField(_("Procentaje para precio de venta"),
                                   max_digits=5, decimal_places=2, blank=True, null=True, default=50.00)
    proveedores = models.ManyToManyField("Proveedor", blank=True,
                                       verbose_name=_("Proveedores"), through=Proveedor.marcas.through)

    objects = PageManager()

    class Meta:
        app_label="shop"
        verbose_name = _("Marca de producto")
        verbose_name_plural = _("Marcas de productos")

class Factura(models.Model):
    numero = CharField(_("Número de factura"), max_length=30)
    fecha = models.DateField()
    foto = models.ImageField(upload_to="facturas")
    monto = fields.MoneyField(_("Total del costo de los productos amparados en la factura"))
    cantidad = models.IntegerField("Cantidad total de artículos")
    descuento = fields.MoneyField(_("Porcentaje del descuento"), default=0.0)
    proveedor = models.ForeignKey("Proveedor")
    terminada = models.BooleanField(default=False, editable=False)

    class Meta:
        app_label="shop"
        unique_together = (("numero", "proveedor"),)

    @property
    def status(self) :
        total = 0 ;  arts = 0

        for surtido in self.surtido_set.all() :
            total =+ sum([pv.cantidad*pv.costo for pv in surtido.moreproductvariation_set.all() if pv.costo is not None])
            arts =+ sum([pv.cantidad for pv in surtido.moreproductvariation_set.all()])

        total = self.monto - total ;  arts = self.cantidad - arts

        if arts == 0  and total.is_zero() :
            return (True, "Terminada")
        return (False, "Pendiente: $ %s (%d arts)" % (total.__str__(), arts))

    def __str__(self):
        return self.proveedor.title + " [" + self.numero + "]"

class Movimiento(Page): 
    destino = models.ManyToManyField("Ubicacion")
    etiquetas_envio = CharField(_("Codigos de barras - envio"), blank=True, null=True, max_length=100000)
    etiquetas_recepcion = CharField(_("Codigos de barras - recepcion"), blank=True, null=True, max_length=100000)
    recibido = models.BooleanField(default=False)

    class Meta:
        app_label="shop"

class Ubicacion(Page):
    movimientos = models.ManyToManyField("Movimiento", blank=True, verbose_name=_("Movimientos"), through=Movimiento.destino.through)
    direccion = CharField(max_length=550, blank=True, null=True)
    telefono= CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label="shop"
        verbose_name_plural = _("Ubicaciones")

class Empleado(User):
    prestamo = fields.MoneyField()
    asignacion = models.ForeignKey(Ubicacion, limit_choices_to = {'parent': None})
    telefono = CharField(max_length=50, blank=True, null=True)

    # Use UserManager to get the create_user method, etc.
    objects = UserManager()

    class Meta:
        app_label="shop"

class Cliente(User):
    credito = fields.MoneyField()
    saldo = fields.MoneyField()
    direccion = CharField(max_length=550, blank=True, null=True)
    telefono = CharField(max_length=50, blank=True, null=True)
    rfc = CharField(max_length=15, blank=True, null=True)
    limite_credito = fields.MoneyField()
    sexo = CharField(max_length=1, choices = (('M', 'Hombre'), ('F', 'Mujer')))
    fecha_nacimiento = models.DateField(blank=True, null=True)
    edad = models.IntegerField(blank=True, null=True)
    #aval = models.ForeignKey(self, blank=True, null=True)

    # Use UserManager to get the create_user method, etc.
    objects = UserManager()

    class Meta:
        app_label="shop"

class Caja(Page):
    fecha_corte =  models.DateTimeField(blank=True, null=True)
    corte =  fields.MoneyField(blank=True, null=True)

    class Meta:
        app_label="shop"

class MovimientoCaja(models.Model):
    cajero = models.ForeignKey(Empleado, related_name="caja_cajero", limit_choices_to = {'groups__name__in': ['Cajero']})
    caja = models.ForeignKey(Caja, default=75)
    cliente = models.ForeignKey("Cliente", default=13, related_name="caja_cliente")
    vendedor = models.ForeignKey(Empleado, related_name="caja_vendedor", limit_choices_to = {'groups__name__in': ['Vendedor']})
    productos = models.ManyToManyField(ProductVariation, blank=True)
    monto_efectivo = fields.MoneyField(_("Monto en efectivo"))
    monto_tarjeta = fields.MoneyField(_("Monto cargado a la tarjeta"))
    codigo_autorizacion = CharField(max_length=50, blank=True, null=True)
    cargo_credito = fields.MoneyField(_("Cargo a credito"))
    cargo_saldo = fields.MoneyField(_("Cargo al saldo del cliente"))
    tipo = models.IntegerField(default=0, choices = ((0, 'Venta'), (1, 'Devolucion'), (2, 'Apartado'), (3, 'Salida de efectivo')))
    date_captured = models.DateTimeField(_("Fecha"), auto_now_add=True)
    estado = models.IntegerField(default=0, choices = ((1, 'Seleccionando'), (2, 'Pagando'), (3, 'Terminada')))

    @property
    def ventas_cliente(self, meses=2):
        return self._base_manager.filter(cliente=self.cliente).filter(date_captured__gt=now()-timedelta(days=61))

    class Meta:
        app_label="shop"
        verbose_name = "Venta"

        
class Nota(models.Model):
    movimiento = models.ForeignKey("MovimientoCaja")
    monto = fields.MoneyField()
    date_reedemed = models.DateTimeField(_("Redimida"), null=True, blank=True)
    es_vale = models.BooleanField(default=False)

    class Meta:
        app_label="shop"

class Gasto(models.Model):
    movimiento = models.ForeignKey("MovimientoCaja")
    beneficiario = models.ForeignKey(User, related_name="gasto_beneficiario", limit_choices_to = {'groups__name__in': ['Cajero', 
                                'Vendedor', 'Almacenista', 'Bodeguero', 'Gerente', 'Socio Catalogo', 'Socio Convenio', 'Proveedor']})
    monto = fields.MoneyField()
    tipo = models.IntegerField(default=0, choices = ((0, 'Comida'), (1, 'A cuenta de nomina'), (2, 'Prestamo'),
                                                     (3, 'Retiro personal'), (4, 'Pago')))
    pago = CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label="shop"

class ProductItem(models.Model):
    label = fields.SKUField(unique=True)
    producto = models.ForeignKey(ProductVariation)
    costo = fields.MoneyField(_("Costo original del producto"), default=0.0)
    ubicaciones = CharField(max_length=500, blank=True, null=True)
    venta = fields.MoneyField(_("Precio al que se vendio"), blank=True, null=True)
    
    class Meta:
        app_label="shop"

