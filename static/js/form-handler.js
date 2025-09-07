/**
 * Manejador universal de formularios para StoraTrack
 * Estandariza el manejo de formularios en toda la aplicación
 */

class FormHandler {
    constructor(formId, options = {}) {
        this.form = document.getElementById(formId);
        this.options = {
            method: 'POST',
            useFormData: true,
            showLoading: true,
            resetOnSuccess: true,
            reloadOnSuccess: true,
            closeModalOnSuccess: true,
            successMessage: 'Operación exitosa',
            errorMessage: 'Error en la operación',
            processData: null, // Callback para procesar datos personalizados
            onSuccess: null, // Callback después del éxito
            onError: null, // Callback para manejo de errores
            reportErrors: false, // Enviar errores a servicio de monitoreo
            timeout: 30000, // Timeout en milisegundos (30 segundos)
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.form) {
            console.error(`Formulario con ID '${this.formId}' no encontrado`);
            return;
        }
        
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.options.showLoading) {
            this.showLoading(true);
        }
        
        try {
            // Ejecutar callback onSubmit si existe
            if (this.options.onSubmit) {
                this.options.onSubmit();
            }
            let url = this.options.url || this.form.action || this.form.getAttribute('data-url');
            
            // Soporte para URLs dinámicas usando función
            if (typeof url === 'function') {
                url = url();
            }
            
            if (!url) {
                throw new Error('URL no especificada para el formulario');
            }
            
            // Crear AbortController para timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.options.timeout);
            
            const requestOptions = {
                method: this.options.method,
                signal: controller.signal,
            };
            
            if (this.options.useFormData) {
                requestOptions.body = new FormData(this.form);
            } else {
                const formData = new FormData(this.form);
                let data;
                
                if (this.options.processData) {
                    // Usar callback personalizado para procesar datos
                    data = this.options.processData(formData);
                } else {
                    // Procesamiento por defecto
                    data = Object.fromEntries(formData.entries());
                    
                    // Manejar checkboxes
                    this.form.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
                        data[checkbox.name] = formData.has(checkbox.name);
                    });
                }
                
                requestOptions.headers = {
                    'Content-Type': 'application/json',
                };
                requestOptions.body = JSON.stringify(data);
            }
            
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                let errorMessage = this.options.errorMessage;
                
                // Manejo específico de códigos de error HTTP
                switch (response.status) {
                    case 400:
                        errorMessage = 'Datos inválidos. Por favor revise la información ingresada.';
                        break;
                    case 401:
                        errorMessage = 'No autorizado. Por favor inicie sesión nuevamente.';
                        break;
                    case 403:
                        errorMessage = 'No tiene permisos para realizar esta acción.';
                        break;
                    case 404:
                        errorMessage = 'Recurso no encontrado.';
                        break;
                    case 409:
                        errorMessage = 'Conflicto: El recurso ya existe o hay un conflicto de datos.';
                        break;
                    case 422:
                        errorMessage = 'Datos de entrada inválidos.';
                        break;
                    case 500:
                        errorMessage = 'Error interno del servidor. Por favor intente más tarde.';
                        break;
                    default:
                        errorMessage = `Error del servidor (${response.status}). Por favor intente más tarde.`;
                }
                
                // Intentar obtener mensaje específico del servidor
                try {
                    const errorData = await response.json();
                    if (errorData.message) {
                        errorMessage = errorData.message;
                    } else if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch (e) {
                    // Si no se puede parsear la respuesta, usar mensaje por defecto
                }
                
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            
            if (result.success !== false) {
                this.handleSuccess(result);
            } else {
                this.handleError(result.message || this.options.errorMessage);
            }
            
        } catch (error) {
            console.error('Error en formulario:', error);
            
            // Manejo específico de errores de red
            let errorMessage = error.message;
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = 'Error de conexión. Por favor verifique su conexión a internet.';
            } else if (error.name === 'AbortError') {
                errorMessage = 'La operación fue cancelada.';
            }
            
            this.handleError(errorMessage || this.options.errorMessage);
        } finally {
            // Limpiar timeout
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
            
            if (this.options.showLoading) {
                this.showLoading(false);
            }
        }
    }
    
    handleSuccess(result) {
        const message = result.message || this.options.successMessage;
        this.showAlert(message, 'success');
        
        if (this.options.resetOnSuccess) {
            this.form.reset();
        }
        
        if (this.options.closeModalOnSuccess) {
            this.closeModal();
        }
        
        if (this.options.reloadOnSuccess) {
            setTimeout(() => location.reload(), 1000);
        }
        
        if (this.options.onSuccess) {
            this.options.onSuccess(result);
        }
    }
    
    handleError(message) {
        // Log del error para debugging
        console.error('FormHandler Error:', {
            formId: this.form?.id,
            url: this.options.url,
            method: this.options.method,
            message: message,
            timestamp: new Date().toISOString()
        });
        
        this.showAlert(message, 'danger');
        
        // Callback personalizado de error
        if (this.options.onError) {
            this.options.onError(message);
        }
        
        // Opcional: Enviar error a servicio de monitoreo
        if (this.options.reportErrors && typeof window.reportError === 'function') {
            window.reportError({
                type: 'form_error',
                formId: this.form?.id,
                message: message,
                url: this.options.url
            });
        }
    }
    
    showLoading(show) {
        const submitBtn = this.form.querySelector('button[type="submit"]');
        if (!submitBtn) return;
        
        if (show) {
            // Guardar texto original si no existe
            if (!submitBtn.hasAttribute('data-original-text')) {
                submitBtn.setAttribute('data-original-text', submitBtn.innerHTML);
            }
            
            // Deshabilitar botón y mostrar loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Procesando...';
            submitBtn.classList.add('loading');
            
            // Deshabilitar todos los inputs del formulario
            const inputs = this.form.querySelectorAll('input, select, textarea, button');
            inputs.forEach(input => {
                if (!input.hasAttribute('data-was-disabled')) {
                    input.setAttribute('data-was-disabled', input.disabled);
                }
                input.disabled = true;
            });
        } else {
            // Restaurar estado original del botón
            submitBtn.disabled = false;
            submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Enviar';
            submitBtn.classList.remove('loading');
            
            // Restaurar estado de inputs
            const inputs = this.form.querySelectorAll('input, select, textarea, button');
            inputs.forEach(input => {
                const wasDisabled = input.getAttribute('data-was-disabled') === 'true';
                input.disabled = wasDisabled;
                input.removeAttribute('data-was-disabled');
            });
        }
    }
    
    closeModal() {
        const modal = this.form.closest('.modal');
        if (modal) {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }
    
    showAlert(message, type) {
        // Usar la función showAlert global si existe
        if (typeof showAlert === 'function') {
            showAlert(message, type);
        } else {
            // Fallback simple
            alert(message);
        }
    }
}

// Función de conveniencia para inicializar formularios
function initForm(formId, options = {}) {
    return new FormHandler(formId, options);
}

// Exportar para uso global
window.FormHandler = FormHandler;
window.initForm = initForm;