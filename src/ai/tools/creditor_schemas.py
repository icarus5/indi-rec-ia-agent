from pydantic import BaseModel, Field

class RegisterClientSchema(BaseModel):
    name: str = Field(..., description="Nombre del cliente (obligatorio)")
    phone_number: str = Field(...,description="Número de teléfono del cliente sin prefijo (obligatorio)")
    code_phone: str = Field(default="PE", description="Código del país del cliente")
    prefix_phone: str = Field(default="+51", description="Prefijo del teléfono del cliente")
    surname: str = Field(default="", description="Apellido del cliente")
    email: str = Field(default="", description="Email del cliente")

class RegisterCollectionSchema(BaseModel):
    name: str = Field(..., description="Nombre del cliente o deudor")
    surname: str = Field(default="", description="Apellido del cliente o deudor")
    code_phone: str = Field(default="PE", description="Código del país del cliente")
    prefix_phone: str = Field(default="+51", description="Prefijo del teléfono del cliente")
    subject: str = Field(..., description="Asunto de la deuda")
    amount: float = Field(..., description="Monto de la deuda, debe ser un numero positivo")
    currency: str = Field(default="Soles (S/)", description="Moneda de la deuda, puede tomar los valores: Soles (S/) o Dolares ($)")
    date: str = Field(..., description="Fecha de la deuda en formato Y-M-D")
    frequency_payment: str = Field(default="ÚNICO", description="Frecuencia del cobro: ÚNICO, SEMANAL, MENSUAL")
    total_quotas: int = Field(default=1, description="Número o total de cuotas de cobro. Positivo, entero máximo 12")
    is_indefinite: bool = Field(default=False, description="Indica si el cobro es indefinido")
    clientPhoneNumber: str = Field(..., description="Telefono del cliente sin incluir el prefijo del telefono")

class RegisterTransferSchema(BaseModel):
    receiver_name: str = Field(..., description="Nombre del receptor de la transferencia")
    receiver_phone: str = Field(None, description="Número de celular del receptor de la transferencia")
    amount: float = Field(..., description="Monto de la transferencia")

class DeleteCollectionSchema(BaseModel):
    collection_id: str = Field(..., description="ID de la colección a eliminar")

class VerifyClientByPhoneNumberSchema(BaseModel):
    phone_number: str = Field(...,description="Número de teléfono del cliente o deudor a ser buscado")

class VerifyClientByNameSchema(BaseModel):
    name: str = Field(...,description="Nombre del cliente o deudor a ser buscado")

class ValidatePhoneNumberSchema(BaseModel):
    prefix_phone: str = Field(default="+51", description="Prefijo del teléfono del cliente, no es obligatorio")
    phone_number: str = Field(...,description="Número de teléfono del cliente sin incluir el prefijo")