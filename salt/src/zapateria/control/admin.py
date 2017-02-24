# -*- coding: utf-8 -*-
from copy import deepcopy
from django.contrib import admin
from django.contrib.messages import info
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.utils.timezone import now
from django.utils.translation import (ugettext, ugettext_lazy as _,
                                      pgettext_lazy as __)
from django.http import HttpResponseRedirect
from django.conf import settings
from cartridge.shop.models import Sale, DiscountCode, Cart, CartItem, ProductVariation, ProductImage
from cartridge.shop.forms import ProductAdminForm, ProductVariationAdminForm, CartItemFormSet
from cartridge.shop.admin import ProductAdmin, ProductImageAdmin, ProductVariationAdmin
from cartridge.shop.utils import recalculate_cart
from mezzanine.core.admin import (DisplayableAdmin,
                                  TabularDynamicInlineAdmin,
                                  BaseTranslationModelAdmin)
from mezzanine.pages.admin import PageAdmin
import elasticsearch
from .models import (Marca, Proveedor, Movimiento, Zapato, Ubicacion, Factura, Surtido, MoreProductVariation, 
                     MovimientoCaja, Gasto, Nota, Caja, Cliente, Empleado, Venta)
from .serializers import ItemSerializer

es_host = settings.ELASTICSEARCH_HOST

class NotaMovimientoAdmin(admin.TabularInline):
    model = Nota
    extra = 1

class GastoMovimientoAdmin(admin.TabularInline):
    model = Gasto
    extra = 1

class MoreProductVariationsInline(admin.TabularInline):
    model = MoreProductVariation
    max_num = None
    extra = 0
    readonly_fields = ["zapato_variation", "costo"]

class MovimientoCajaUserAdmin(admin.TabularInline):
    model = MovimientoCaja
    #fields = ["productos", "detalles",]
    #readonly_fields = ["ventas_cliente",]
    readonly_fields = ["detalles",]
    extra = 0

    def detalles(self, obj) :
        return self.request.cart.total()

    detalles.allow_tags = True
    detalles.short_description = 'Cargo'

class ZapatoSurtidoAdmin(admin.TabularInline):
    model = Surtido
    fields = ["factura", "detalles", "editar"]
    readonly_fields = ["detalles", "editar"]
    extra = 1

    def detalles(self, obj) :

        if obj.terminado :
            total = 0

            for pv in obj.moreproductvariation_set.all():
                total += pv.cantidad
            return "Total: %d" % total

        lista = ""

        for it in [pv.zapato_variation.option2.__str__() + "(" + pv.zapato_variation.option1.__str__() + ")" + " : <a href=/admin/shop/moreproductvariation/%d/>" % pv.id + pv.cantidad.__str__() + "</a></br>" for pv in obj.moreproductvariation_set.all()]:
            lista += it

        return lista

    detalles.allow_tags = True
    detalles.short_description = 'Variaciones'

    def editar(self, obj) :
        link = ""

        if obj.terminado :
            return "<a href=/admin/shop/surtido/%d/>Listar</a>" % obj.id
        if obj.id :
            link = "<a href=/admin/shop/surtido/%d/>Editar</a>" % obj.id
        return link

    editar.allow_tags = True
    editar.short_description = 'Acciones'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "factura" and request.resolver_match.args:
            self_pub_id = request.resolver_match.args[0]
            todas = Factura.objects.select_related("proveedor").all()
            for fac in todas:
                if fac.surtido_set.filter(producto_id=self_pub_id) == []:
                    todas.exclude(fac)
            kwargs["queryset"] = todas | Factura.objects.select_related("proveedor").filter(terminada=False)
        return super(ZapatoSurtidoAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class MovimientoCajaAdmin(admin.ModelAdmin):
    inlines = (GastoMovimientoAdmin, NotaMovimientoAdmin)
    radio_fields = {"tipo": admin.HORIZONTAL, "caja": admin.VERTICAL,}

    def save_model(self, request, obj, form, change):
        super(MovimientoCajaAdmin, self).save_model(request, obj, form, change)
        request.cart = Venta.objects.from_request(request)
        for prod in obj.productos.all():
            request.cart.otro_item(prod)
            recalculate_cart(request)
        info(request, _("se agregó %s" % [cit.description for cit in request.cart].__str__()))

class MoreProductVariationAdmin(admin.ModelAdmin):
    model = MoreProductVariation
    search_fields = ('zapato_variation', 'surtido', 'date_captured')
    list_display = ('date_captured',)
    fields = ('cantidad',)

    def in_menu(self):
        return False

    def response_post_save_change(self, request, obj):
        return HttpResponseRedirect('/admin/shop/zapato/%d/' % obj.surtido.producto.id)

class FacturaAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'numero', 'estado')

    def estado(self, obj):
        return obj.status[1]

    def get_readonly_fields(self, request, obj=None) :
        if obj is not None :
            if obj.status[0] and obj.terminada:
                return [f.name for f in self.model._meta.fields]
            return ['foto']

        elif self.declared_fieldsets:
            return flatten_fieldsets(self.declared_fieldsets)

        else :
            return self.readonly_fields

    def save_model(self, request, obj, form, change):
        super(FacturaAdmin, self).save_model(request, obj, form, change)
        if obj.status[0]:
            obj.terminada = True
            obj.save()

class SurtidoAdmin(admin.ModelAdmin):
    readonly_fields = ('producto', 'color_original', 'factura', 'lista')
    inlines = (MoreProductVariationsInline,)
    list_display = ('producto', 'date_captured', 'factura', 'terminado', )
    list_filter = ["producto__marcas", "factura__proveedor"]

    def get_queryset(self, request) :
        qs = super(SurtidoAdmin, self).get_queryset(request)
        return qs.order_by('-pk')

    def color_original(self, obj) :
        return obj.producto.color_original

    def lista(self, obj) :
        list = ""

        if obj.terminado :
            list += "<table><tr><th>Cantidad</th><th>Producto</th><th>Precio al publico</th></tr>"
            for mpvi in [mpv for mpv in obj.moreproductvariation_set.all() if mpv.cantidad !=0 ] :
                if mpvi.zapato_variation.on_sale() : 
                    precio = mpvi.zapato_variation.price()
                else :
                    precio = mpvi.zapato_variation.unit_price * ( 1 + mpvi.zapato_variation.product.zapato.marcas.cargo/100 )
                list += "<tr><td>%d</td><td>%s</td><td>%d</td></tr>" %(mpvi.cantidad, mpvi.zapato_variation.__unicode__(), precio)
            list += "</table>"
        return list

    lista.allow_tags = True

    def get_inline_instances(self, request, obj=None) :

        if obj is not None :
            if obj.terminado :
                return ()

        return super(SurtidoAdmin, self).get_inline_instances(request, obj)

    def get_readonly_fields(self, request, obj=None) :

        if obj is not None :
            if obj.terminado : 
                return self.readonly_fields.__add__(('terminado',))

        return self.readonly_fields


    def save_model(self, request, obj, form, change):
        super(SurtidoAdmin, self).save_model(request, obj, form, change)
        #obj.save()

        if obj.terminado :
            es = elasticsearch.Elasticsearch(es_host)
            etiquetas = []

            for mpv_o in obj.moreproductvariation_set.all() :
                mpv = mpv_o.zapato_variation

                if mpv.num_in_stock is not None :
                    mpv.num_in_stock += mpv_o.cantidad
                else :
                    mpv.num_in_stock = mpv_o.cantidad
                mpv.save()
                # crea etiquetas y movimiento
                prelabel = 'YWWD' + 'id' + 'rd'
                for it in range(mpv_o.cantidad):
                    item = ItemSerializer({'surtido_id': obj.id, 'variation_id': mpv.id, 'cost': mpv.price(), 
                                       'ingresed_by': request.user.id, 'ingresed': now(), 'sku': mpv.sku,
                                       'etiqueta': prelabel + it.__str__(),
                                       'current_location': request.user.empleado.asignacion.id,
                                       'location_list': '%d' %request.user.empleado.asignacion.id, 'status': 0,
                                       'proveedor': obj.factura.proveedor.title, 'color':  mpv.option2,
                                       'marca': mpv.product.zapato.marcas.title, 'linea': mpv.option3,
                                       'color_original': mpv.product.zapato.color_original, 'talla': mpv.option1 })

                    label = es.index(index='productos', doc_type='product_item', body=item.data)
                    # genera etiquetas
                    etiquetas.append((label['_id'],mpv.product.zapato.__repr__(),
                                      mpv.option2,mpv.option1,mpv.product.title))

            mo = Movimiento.objects.create(title="Surtido: " + obj.producto.marcas.codigo + 
                                           obj.producto.codigo.__str__(),
                                           recibido=True,etiquetas_recepcion=etiquetas,login_required=True,in_menus=[])
            mo.destino.add(request.user.empleado.asignacion.id)    
            info(request, _("Etiquetas listas para impresión"))

    def response_post_save_change(self, request, obj):

        return HttpResponseRedirect('/admin/shop/zapato/%d/' % obj.producto.id)

class MovimientoAdmin(admin.ModelAdmin):
    readonly_fields = ('title', 'destino')
    list_display = ('movimiento', 'recibido', 'publish_date')
    list_filter = ["recibido","destino"]

    def get_queryset(self, request) :
        qs = super(MovimientoAdmin, self).get_queryset(request).none()
        return qs.order_by('-pk')

    def save_model(self, request, obj, form, change) :

        super(MovimientoAdmin, self).save_model(request, obj, form, change)
        if not obj.title :
            obj.title = request.user.empleado.asignacion.title + " - " + form.cleaned_data["destino"][0].title

            info(request, _("Delivery ready to be sent"))

        if request.POST.get("etiquetas_recepcion") :
            obj.recibido = True
            obj.login_required = True
            obj.in_menus=[]

        obj.save()

    def get_fieldsets(self, request, obj=None) :
        movimiento_fieldsets = deepcopy(product_fieldsets)

        movimiento_fieldsets[0][1]["fields"].extend(["destino",])
        if obj is None :

            movimiento_fieldsets[0][1]["fields"].extend(["etiquetas_envio",])
        elif not obj.recibido :

            movimiento_fieldsets[0][1]["fields"].extend(["etiquetas_recepcion",])
        else:

            movimiento_fieldsets[0][1]["fields"].extend(["validacion",])

        movimiento_fieldsets = list(movimiento_fieldsets)

        movimiento_fieldsets.pop()
        return movimiento_fieldsets

    def get_readonly_fields(self, request, obj=None) :

        if obj is not None :

            if obj.recibido : 

                return self.readonly_fields.__add__(('validacion',))
            else :

                return self.readonly_fields
        return ('title',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "destino" :
            lugar = request.user.empleado.asignacion
            kwargs["queryset"] = Ubicacion.objects.filter(parent=None).exclude(pk=lugar.pk)|Ubicacion.objects.filter(parent=lugar).filter(title__in=['Apartado', 'Aparador'])
        return super(MovimientoAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def validacion(self, obj) :
        valid = ""

        if obj.etiquetas_envio is None :
            return "Solo recepcion"

        env = obj.etiquetas_envio.split(",")
        rec = obj.etiquetas_recepcion.split(",")
        faltan = [et for et in env if et not in rec]
        sobran = [et for et in rec if et not in env]

        if faltan != [] : 
            valid += "Faltan:" 

            for fal in faltan: valid += " " + fal

            valid += "</br>" 
        if sobran != [] : 
            valid += "Sobran:" 

            for sob in sobran: valid += " " + sob
        if valid == "" : return "Correcto"
        return valid

    validacion.allow_tags = True


user_fieldsets = deepcopy(UserAdmin.fieldsets)
user_fieldsets[1][1]["fields"] = user_fieldsets[1][1]["fields"].__add__(('telefono',))
user_fieldsets[2][1]["fields"] = ("groups",)

class EmpleadoAdmin(UserAdmin) :
    list_display = ('username', 'email', 'first_name', 'last_name', 'telefono', 'prestamo', 'asignacion')
    readonly_fields = ('last_login', 'date_joined')
    empleado_fieldsets = deepcopy(user_fieldsets)
    empleado_fieldsets[2][1]["fields"] = empleado_fieldsets[2][1]["fields"].__add__(('asignacion',))
    fieldsets = empleado_fieldsets

    def save_model(self, request, obj, form, change):
        obj.is_staff = True

        obj.save()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups" :
            kwargs["queryset"] = Group.objects.filter(name__in=['Vendedor', 'Cajero', 'Bodeguero']) #Alamcenista, Gerente
        return super(EmpleadoAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

class ClienteAdmin(UserAdmin) : 
    list_display = ('username', 'email', 'first_name', 'last_name', 'telefono','credito', 'tipo')
    readonly_fields = ('last_login', 'date_joined')
    cliente_fieldsets = deepcopy(user_fieldsets)
    cliente_fieldsets[1][1]["fields"] = cliente_fieldsets[1][1]["fields"].__add__(('direccion',))
    cliente_fieldsets[2][1]["fields"] = cliente_fieldsets[2][1]["fields"].__add__(('saldo', 'credito'))
    fieldsets = cliente_fieldsets
    inlines = (MovimientoCajaUserAdmin,)

    def tipo(self, obj):
        """
        get group, separate by comma, and display empty string if user has no group
        """
        return ','.join([g.name for g in obj.groups.all()]) if obj.groups.count() else ''

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups" :
            kwargs["queryset"] = Group.objects.filter(name__in=['Socio Catalogo', 'Socio Convenio', 'Proveedor'])
        return super(ClienteAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.is_staff = False
        obj.is_active = False

        obj.save()

product_fieldsets = deepcopy(DisplayableAdmin.fieldsets)
product_fieldsets[0][1]["fields"].remove("status")
product_fieldsets[0][1]["fields"].pop()

class UbicacionAdmin(PageAdmin):
    ubicacion_fieldsets = deepcopy(product_fieldsets)
    ubicacion_fieldsets = list(ubicacion_fieldsets)
    ubicacion_fieldsets.pop()
    fieldsets = ubicacion_fieldsets

    def save_model(self, request, obj, form, change):

        obj.save()

class MarcaAdmin(PageAdmin):
    marca_fieldsets = deepcopy(product_fieldsets)
    marca_fieldsets[0][1]["fields"].extend(["codigo", "cargo", "proveedores"])
    marca_fieldsets = list(marca_fieldsets)
    marca_fieldsets.pop()
    fieldsets = marca_fieldsets
    filter_horizontal = ("proveedores",)

    def get_queryset(self, request) :
        qs = super(MarcaAdmin, self).get_queryset(request)
        return qs.order_by('title')

    def save_model(self, request, obj, form, change):

        obj.save()

class ProveedorAdmin(PageAdmin):
    proveedor_fieldsets = deepcopy(product_fieldsets)
    proveedor_fieldsets[0][1]["fields"].extend(["telefono", "direccion", "rfc", "correo", "url", "contacto", "marcas"])
    proveedor_fieldsets = list(proveedor_fieldsets)
    proveedor_fieldsets.pop()
    fieldsets = proveedor_fieldsets
    filter_horizontal = ("marcas",)

    def get_queryset(self, request) :
        qs = super(ProveedorAdmin, self).get_queryset(request)
        return qs.order_by('title')

    def save_model(self, request, obj, form, change):

        obj.save()

class ZapatoAdmin(ProductAdmin):
    class Meta:
        model = Zapato

    class Media:
        js = ("cartridge/js/admin/product_variations.js",)
        css = {"all": ("cartridge/css/admin/product.css",)}

    list_editable = []
    zapato_fieldsets = deepcopy(ProductAdmin.fieldsets)
    zapato_fieldsets[0][1]["fields"].remove("status")
    zapato_fieldsets[0][1]["fields"].remove("available")
    zapato_fieldsets[0][1]["fields"].remove("content")
    zapato_fieldsets[0][1]["fields"].remove("categories")
    zapato_fieldsets[0][1]["fields"].pop()
    zapato_fieldsets[0][1]["fields"].extend(["color_original", "marcas", "codigo", ])#"codigo_proveedor"])
    zapato_fieldsets = list(zapato_fieldsets)
    zapato_fieldsets.pop()
    fieldsets = zapato_fieldsets 
    exclude = ("login_required", "in_menus", "status", "available")
    inlines = (ProductVariationAdmin, ZapatoSurtidoAdmin, ProductImageAdmin)
    list_display = ('title', 'marcas', 'color_original', 'codigo', 'stock', 'admin_thumb')
    list_filter = ["marcas","marcas__proveedores"]
    search_fields = ['title', 'marcas__title', 'codigo', 'marcas__proveedores__title']
    form = ProductAdminForm

    def status(self, obj):
        pass

    def available(self, obj):
        pass

    def save_model(self, request, obj, form, change):
        """
        Store the product object for creating variations in save_formset.
        """
        super(ZapatoAdmin, self).save_model(request, obj, form, change)
        self._product = obj

    def save_formset(self, request, form, formset, change):

        if formset.model == Surtido :
            obj = form.save(commit=False) 
            surs = formset.save(commit=False)

            for sur in surs :
                if obj.pedido_set.filter(id=sur.id) :
                    if obj.pedido_set.get(id=sur.id).surtido.factura != sur.factura :
                        info(request, _("no se puede cambiar la factura" ))
                        return request
                else :
                    formset.save()

                for variation_id in [ mpv.id for mpv in obj.variations.all() if mpv.id not in 
                    [ pv.zapato_variation.id for pv in sur.moreproductvariation_set.all()]]: 
                    variation = ProductVariation.objects.get(id=variation_id)

                    sur.moreproductvariation_set.create(zapato_variation_id=variation_id, costo=variation.unit_price)
                sur.save()            
            formset.save()

        else:

            super(ProductAdmin, self).save_formset(request, form, formset,
                                                   change)
            if formset.model == ProductVariation :
                option_fields = [f.name for f in ProductVariation.option_fields()]
                options = dict([(f, request.POST.getlist(f)) for f in option_fields
                                if request.POST.getlist(f)])

                self._product.variations.create_from_options(options)


#admin.site.unregister(Sale)
#admin.site.unregister(DiscountCode)
admin.site.register(Cart)
admin.site.register(Caja)
admin.site.register(Ubicacion, UbicacionAdmin)
admin.site.register(Factura, FacturaAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Empleado, EmpleadoAdmin)
admin.site.register(MovimientoCaja, MovimientoCajaAdmin)
admin.site.register(Surtido, SurtidoAdmin)
admin.site.register(MoreProductVariation,MoreProductVariationAdmin)
admin.site.register(Movimiento, MovimientoAdmin)
admin.site.register(Zapato, ZapatoAdmin)
admin.site.register(Marca, MarcaAdmin)
admin.site.register(Proveedor, ProveedorAdmin)
