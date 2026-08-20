from decimal import Decimal

from django.conf import settings
from django.db import models


class Perfil(models.Model):
    """Datos adicionales de rol para cada usuario de Django (auth.User)."""

    class Rol(models.TextChoices):
        TRABAJADOR = "TRABAJADOR", "Trabajador"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.TRABAJADOR)
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervisados",
        help_text="Supervisor asignado a este trabajador (si aplica).",
    )

    def __str__(self):
        nombre = self.usuario.get_full_name() or self.usuario.username
        return f"{nombre} ({self.get_rol_display()})"


class Anticipo(models.Model):
    codigo = models.CharField(
        max_length=30, unique=True, help_text="Ej. ANT-2026-00126"
    )
    empleado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="anticipos"
    )
    fecha = models.DateField()
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    concepto = models.TextField(blank=True)
    proyecto = models.CharField(max_length=120, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anticipos_creados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-creado_en"]

    def __str__(self):
        return f"{self.codigo} · {self.empleado} · {self.valor}"

    @property
    def legalizacion_o_ninguna(self):
        return getattr(self, "legalizacion", None)

    @property
    def estado(self):
        """Estado derivado: si no tiene legalización todavía, está pendiente."""
        leg = self.legalizacion_o_ninguna
        return leg.estado if leg else "pendiente"

    @property
    def estado_display(self):
        if self.estado == "pendiente":
            return "Pendiente por legalizar"
        return self.legalizacion.get_estado_display()

    @property
    def valor_presentado(self):
        leg = self.legalizacion_o_ninguna
        return leg.valor_presentado if leg else Decimal("0")

    @property
    def valor_reconocido(self):
        leg = self.legalizacion_o_ninguna
        if leg and leg.valor_reconocido is not None:
            return leg.valor_reconocido
        return Decimal("0")

    @property
    def saldo_pendiente(self):
        return self.valor - self.valor_reconocido


class Legalizacion(models.Model):
    class Estado(models.TextChoices):
        REVISION = "revision", "En espera de respuesta de SALT"
        APROBADA = "aprobada", "Aprobada (todo reconocido)"
        PARCIAL = "parcial", "Aprobada parcialmente"
        RECHAZADA = "rechazada", "Rechazada"

    class Origen(models.TextChoices):
        MANUAL = "manual", "Registro manual"
        OUTLOOK = "outlook", "Detectado en Outlook"
        GMAIL = "gmail", "Detectado en Gmail"

    class MotivoDevolucion(models.TextChoices):
        SOPORTE = "soporte", "Factura no válida / soporte incompleto"
        CUENTA = "cuenta", "Cuenta bancaria inconsistente"
        CONCEPTO = "concepto", "Concepto no corresponde al anticipo"
        OTRO = "otro", "Otro"

    anticipo = models.OneToOneField(
        Anticipo, on_delete=models.CASCADE, related_name="legalizacion"
    )
    codigo = models.CharField(
        max_length=30, unique=True, help_text="Ej. LEG-2026-00079"
    )
    fecha_presentado = models.DateField()
    valor_presentado = models.DecimalField(max_digits=14, decimal_places=2)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.REVISION
    )
    valor_reconocido = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    motivo_devolucion = models.CharField(
        max_length=20, choices=MotivoDevolucion.choices, blank=True
    )
    fecha_resultado = models.DateField(null=True, blank=True)
    origen = models.CharField(
        max_length=10, choices=Origen.choices, default=Origen.MANUAL
    )
    mensaje_id_correo = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID del correo (Outlook/Gmail) que originó este registro, si aplica.",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_presentado"]

    def __str__(self):
        return f"{self.codigo} · {self.anticipo.codigo}"

    @property
    def valor_devuelto(self):
        if self.valor_reconocido is None:
            return Decimal("0")
        return max(Decimal("0"), self.valor_presentado - self.valor_reconocido)


class Archivo(models.Model):
    class Tipo(models.TextChoices):
        EXCEL = "excel", "Excel de legalización"
        PDF = "pdf", "PDF de facturas / recibos"
        CORREO = "correo", "Correo"
        OTRO = "otro", "Otro soporte"

    anticipo = models.ForeignKey(
        Anticipo, on_delete=models.CASCADE, related_name="archivos"
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.OTRO)
    archivo = models.FileField(upload_to="documentos/%Y/%m/")
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-subido_en"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.anticipo.codigo}"


class Reclamo(models.Model):
    class Estado(models.TextChoices):
        ABIERTO = "abierto", "Abierto"
        RESUELTO = "resuelto", "Resuelto"

    legalizacion = models.ForeignKey(
        Legalizacion, on_delete=models.CASCADE, related_name="reclamos"
    )
    codigo = models.CharField(max_length=30)
    factura = models.CharField(max_length=60, blank=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.ABIERTO
    )
    fecha = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.codigo} · {self.legalizacion.codigo}"