document.addEventListener("alpine:init", () => {
  Alpine.data("app", () => ({
    // State
    loading: false,
    isAuthenticated: false,
    user: null,
    currentPage: 'dashboard',
    authMode: 'login',

    // Menu - computed dynamically based on user role
    get primaryMenu() {
      const baseMenu = [
        {
          title: "Dashboard",
          icon: "home",
          route: "dashboard"
        },
        {
          title: "Eventi",
          icon: "event",
          route: "events"
        },
        {
          title: "Associazioni",
          icon: "groups",
          route: "associations"
        }
      ];

      // Only show reports for admin and superadmin users
      if (this.canAdmin()) {
        baseMenu.push({
          title: "Riepilogo",
          icon: "leaderboard",
          route: "reports"
        });
      }

      return baseMenu;
    },

    // Toast
    toast: {
      show: false,
      message: '',
      type: 'info'
    },

    // Data
    events: [],
    associations: [],
    volunteers: [],
    reports: {},
    stats: {
      totalEvents: 0,
      totalAssociations: 0,
      totalRevenue: 0,
      totalVolunteers: 0
    },
    recentEvents: [],

    // Forms
    loginForm: {
      username: '',
      password: ''
    },
    registerForm: {
      username: '',
      email: '',
      password: ''
    },
    eventForm: {},
    eventFormDefaults: {
      title: '',
      start_datetime: '',
      end_datetime: '',
      location: '',
      stage_size: '',
      requester: '',
      request_received_date: '',
      assembly_datetime: '',
      disassembly_datetime: '',
      status: 'To Be Scheduled'
    },
    associationForm: {},
    associationFormDefaults: {
      name: '',
      contact_person: '',
      tax_code: '',
      iban: '',
      headquarters: ''
    },
    volunteerForm: {
      first_name: '',
      last_name: '',
      date_of_birth: '',
      is_certified: false
    },
    userEditForm: {
      username: '',
      email: '',
      password: ''
    },

    // Modals
    showEventModal: false,
    showAssociationModal: false,
    showVolunteerModal: false,
    showEventDetailsModal: false,
    showEditUserModal: false,

    // Filters
    eventFilters: {
      status: ''
    },

    // Selected items
    selectedAssociation: null,
    selectedEvent: null,

    // Event Assignment Form
    eventAssignmentForm: {
      association_id: '',
      volunteer_count: 1,
      volunteer_ids: []
    },

    // API Base URL
    apiUrl: '/api/v1',

    // Initialize
    async init() {
      // Handle URL fragments for navigation
      this.handleUrlFragment();
      
      const token = localStorage.getItem('token');
      if (token) {
        this.setAuthToken(token);
        try {
          await this.loadUser();
          this.isAuthenticated = true;
          await this.loadInitialData();
        } catch (error) {
          localStorage.removeItem('token');
          this.isAuthenticated = false;
        }
      }
      
      // Listen for URL changes
      window.addEventListener('hashchange', () => {
        this.handleUrlFragment();
      });
    },

    // API Helper with improved error handling
    async apiCall(endpoint, options = {}) {
      // Don't show global loading for certain operations
      const showGlobalLoading = options.showLoading !== false;
      if (showGlobalLoading) this.loading = true;

      try {
        const token = localStorage.getItem('token');
        const config = {
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
          },
          ...options
        };

        // Add timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        config.signal = controller.signal;

        const response = await fetch(this.apiUrl + endpoint, config);
        clearTimeout(timeoutId);

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
          } catch {
            errorData = { detail: `Errore HTTP ${response.status}` };
          }

          // Handle specific error types
          if (response.status === 401) {
            this.handleAuthError();
            throw new Error('Sessione scaduta. Effettua nuovamente il login.');
          } else if (response.status === 403) {
            throw new Error('Non hai i permessi per eseguire questa operazione.');
          } else if (response.status >= 500) {
            throw new Error('Errore del server. Riprova tra qualche minuto.');
          }

          const errorMessage = this.formatErrorMessage(errorData);
          throw new Error(errorMessage);
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        }

        return null;
      } catch (error) {
        if (error.name === 'AbortError') {
          throw new Error('Richiesta scaduta. Controlla la connessione.');
        }
        throw error;
      } finally {
        if (showGlobalLoading) this.loading = false;
      }
    },

    formatErrorMessage(errorData) {
      if (typeof errorData === 'string') return errorData;
      if (errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          return errorData.detail.map(err => err.msg || err).join(', ');
        }
        return errorData.detail;
      }
      return 'Si è verificato un errore.';
    },

    handleAuthError() {
      localStorage.removeItem('token');
      this.isAuthenticated = false;
      this.user = null;
      this.currentPage = 'dashboard';
    },

    resetForms() {
      this.loginForm = { username: '', password: '' };
      this.registerForm = { username: '', email: '', password: '' };
    },

    // Authentication
    setAuthToken(token) {
      localStorage.setItem('token', token);
    },

    async login() {
      // Validate form
      const errors = this.validateForm(this.loginForm, {
        username: { required: true, label: 'Username', minLength: 2 },
        password: { required: true, label: 'Password', minLength: 3 }
      });

      if (errors.length > 0) {
        this.showToast(errors[0], 'error');
        return;
      }

      try {
        const response = await this.apiCall('/auth/login', {
          method: 'POST',
          body: JSON.stringify(this.loginForm)
        });

        this.setAuthToken(response.access_token);
        await this.loadUser();
        this.isAuthenticated = true;
        await this.loadInitialData();
        this.showToast('🎉 Benvenuto! Login effettuato con successo.', 'success');
        this.resetForms();
      } catch (error) {
        this.showToast(error.message, 'error');
      }
    },

    async register() {
      // Validate form
      const errors = this.validateForm(this.registerForm, {
        username: { required: true, label: 'Username', minLength: 3 },
        email: { required: true, label: 'Email', email: true },
        password: { required: true, label: 'Password', minLength: 6 }
      });

      if (errors.length > 0) {
        this.showToast(errors[0], 'error');
        return;
      }

      try {
        await this.apiCall('/auth/register', {
          method: 'POST',
          body: JSON.stringify(this.registerForm)
        });

        this.showToast('🎉 Account creato con successo! Ora puoi effettuare il login.', 'success');
        this.authMode = 'login';
        this.resetForms();
        // Pre-fill username in login form
        this.loginForm.username = this.registerForm.username;
      } catch (error) {
        this.showToast(error.message, 'error');
      }
    },

    async loadUser() {
      this.user = await this.apiCall('/auth/me');
      this.userEditForm = {
        username: this.user.username,
        email: this.user.email
      };
    },

    async updateUser() {
      try {
        // Validate form
        const errors = this.validateForm(this.userEditForm, {
          username: { required: true, label: 'Username', minLength: 3 },
          email: { required: true, label: 'Email', email: true }
        });

        if (errors.length > 0) {
          this.showToast(errors[0], 'error');
          return;
        }

        // Prepare update data - only send fields that have values
        const updateData = {
          username: this.userEditForm.username,
          email: this.userEditForm.email
        };

        // Only include password if it's provided
        if (this.userEditForm.password && this.userEditForm.password.trim() !== '') {
          updateData.password = this.userEditForm.password;
        }

        const updatedUser = await this.apiCall('/auth/me', {
          method: 'PUT',
          body: JSON.stringify(updateData)
        });

        // Update local user data
        this.user = updatedUser;
        this.showEditUserModal = false;

        // Reset password field
        this.userEditForm.password = '';

        this.showToast('✅ Profilo aggiornato con successo', 'success');
      } catch (error) {
        this.showToast('Errore nell\'aggiornamento: ' + error.message, 'error');
      }
    },

    logout() {
      localStorage.removeItem('token');
      this.isAuthenticated = false;
      this.user = null;
      this.currentPage = 'dashboard';
      this.showToast('👋 Logout effettuato', 'info');
    },

    // Data Loading with error handling
    async loadInitialData() {
      try {
        // Load essential data first
        await Promise.all([
          this.loadAssociations(),
          this.loadEvents()
        ]);

        // Load secondary data
        await Promise.all([
          this.loadReports().catch(err => console.warn('Reports loading failed:', err)),
          this.loadStats().catch(err => console.warn('Stats loading failed:', err))
        ]);
      } catch (error) {
        this.showToast('Errore nel caricamento dei dati: ' + error.message, 'error');
      }
    },

    async loadEvents() {
      try {
        const params = new URLSearchParams();
        if (this.eventFilters.status) {
          params.append('status', this.eventFilters.status);
        }
        this.events = await this.apiCall('/events/?' + params.toString(), { showLoading: false });
        this.recentEvents = this.events.slice(0, 20);
        this.updateEventStats();
      } catch (error) {
        this.showToast('Errore nel caricamento eventi: ' + error.message, 'error');
        this.events = [];
        this.recentEvents = [];
      }
    },

    async loadAssociations() {
      try {
        this.associations = await this.apiCall('/associations/', { showLoading: false });
        this.updateAssociationStats();
      } catch (error) {
        this.showToast('Errore nel caricamento associazioni: ' + error.message, 'error');
        this.associations = [];
      }
    },

    async loadReports() {
      try {
        this.reports = await this.apiCall('/reports/', { showLoading: false });
      } catch (error) {
        console.warn('Reports loading failed:', error);
        this.reports = {};
      }
    },

    async loadStats() {
      try {
        await this.loadReports();
        this.updateStats();
      } catch (error) {
        console.warn('Stats loading failed:', error);
      }
    },

    updateStats() {
      this.stats = {
        totalEvents: this.reports.overall_totals?.total_events || this.events.length || 0,
        totalAssociations: this.associations.length || 0,
        totalRevenue: this.reports.overall_totals?.total_revenue || 0,
        totalVolunteers: this.associations.reduce((sum, assoc) => sum + (assoc.volunteers?.length || 0), 0)
      };
    },

    updateEventStats() {
      this.stats.totalEvents = this.events.length;
    },

    updateAssociationStats() {
      this.stats.totalAssociations = this.associations.length;
      this.stats.totalVolunteers = this.associations.reduce((sum, assoc) => sum + (assoc.volunteers?.length || 0), 0);
    },

    async loadVolunteers(associationId) {
      this.volunteers = await this.apiCall(`/associations/${associationId}/volunteers`);
    },

    // Events
    async saveEvent() {
      try {
        const method = this.eventForm.id ? 'PUT' : 'POST';
        const endpoint = this.eventForm.id ? `/events/${this.eventForm.id}` : '/events/';

        await this.apiCall(endpoint, {
          method,
          body: JSON.stringify(this.eventForm)
        });

        this.showEventModal = false;
        await this.loadEvents();
        this.showToast(this.eventForm.id ? '✅ Evento aggiornato' : '✅ Evento creato', 'success');
      } catch (error) {
        this.showToast('Errore: ' + error.message, 'error');
      }
    },

    editEvent(event) {
      this.eventForm = { ...event };
      this.eventForm.start_datetime = this.formatDateTimeLocal(event.start_datetime);
      this.eventForm.end_datetime = this.formatDateTimeLocal(event.end_datetime);
      this.eventForm.request_received_date = this.formatDateTimeLocal(event.request_received_date);
      if (event.assembly_datetime) {
        this.eventForm.assembly_datetime = this.formatDateTimeLocal(event.assembly_datetime);
      }
      if (event.disassembly_datetime) {
        this.eventForm.disassembly_datetime = this.formatDateTimeLocal(event.disassembly_datetime);
      }
      this.showEventModal = true;
    },

    async deleteEvent(eventId) {
      if (confirm('Sei sicuro di voler eliminare questo evento?')) {
        try {
          await this.apiCall(`/events/${eventId}`, { method: 'DELETE' });
          await this.loadEvents();
          this.showToast('✅ Evento eliminato', 'success');
        } catch (error) {
          this.showToast('Errore: ' + error.message, 'error');
        }
      }
    },

    async viewEventDetails(event) {
      // Load full event details including associations
      try {
        this.selectedEvent = await this.apiCall(`/events/${event.id}`);
        this.eventAssignmentForm = {
          association_id: '',
          volunteer_count: 1,
          volunteer_ids: []
        };
        this.showEventDetailsModal = true;
      } catch (error) {
        this.showToast('Errore nel caricamento dettagli: ' + error.message, 'error');
      }
    },

    async assignAssociationToEvent() {
      try {
        await this.apiCall(`/events/${this.selectedEvent.id}/associations`, {
          method: 'POST',
          body: JSON.stringify(this.eventAssignmentForm)
        });

        // Reload event details
        this.selectedEvent = await this.apiCall(`/events/${this.selectedEvent.id}`);

        // Reset form
        this.eventAssignmentForm = {
          association_id: '',
          volunteer_count: 1,
          volunteer_ids: []
        };

        await this.loadEvents(); // Refresh events list
        this.showToast('✅ Associazione assegnata all\'evento', 'success');
      } catch (error) {
        this.showToast('Errore: ' + error.message, 'error');
      }
    },

    async removeAssociationFromEvent(associationId) {
      if (confirm('Sei sicuro di voler rimuovere questa associazione dall\'evento?')) {
        try {
          await this.apiCall(`/events/${this.selectedEvent.id}/associations/${associationId}`, {
            method: 'DELETE'
          });

          // Reload event details
          this.selectedEvent = await this.apiCall(`/events/${this.selectedEvent.id}`);
          await this.loadEvents(); // Refresh events list
          this.showToast('✅ Associazione rimossa dall\'evento', 'success');
        } catch (error) {
          this.showToast('Errore: ' + error.message, 'error');
        }
      }
    },

    getAssociationVolunteers(associationId) {
      if (!associationId) return [];
      const association = this.associations.find(a => a.id == associationId);
      return association?.volunteers || [];
    },

    // Associations
    async saveAssociation() {
      try {
        const method = this.associationForm.id ? 'PUT' : 'POST';
        const endpoint = this.associationForm.id ? `/associations/${this.associationForm.id}` : '/associations/';

        await this.apiCall(endpoint, {
          method,
          body: JSON.stringify(this.associationForm)
        });

        this.showAssociationModal = false;
        await this.loadAssociations();
        this.showToast(this.associationForm.id ? '✅ Associazione aggiornata' : '✅ Associazione creata', 'success');
      } catch (error) {
        this.showToast('Errore: ' + error.message, 'error');
      }
    },

    editAssociation(association) {
      this.associationForm = { ...association };
      this.showAssociationModal = true;
    },

    async deleteAssociation(associationId) {
      if (confirm('Sei sicuro di voler eliminare questa associazione?')) {
        try {
          await this.apiCall(`/associations/${associationId}`, { method: 'DELETE' });
          await this.loadAssociations();
          this.showToast('✅ Associazione eliminata', 'success');
        } catch (error) {
          this.showToast('Errore: ' + error.message, 'error');
        }
      }
    },

    async manageVolunteers(association) {
      this.selectedAssociation = association;
      await this.loadVolunteers(association.id);
      this.showVolunteerModal = true;
    },

    // Volunteers
    async addVolunteer() {
      try {
        // Prepare volunteer data, converting empty date to null
        const volunteerData = {
          ...this.volunteerForm,
          date_of_birth: this.volunteerForm.date_of_birth || null
        };

        await this.apiCall(`/associations/${this.selectedAssociation.id}/volunteers`, {
          method: 'POST',
          body: JSON.stringify(volunteerData)
        });

        this.volunteerForm = {
          first_name: '',
          last_name: '',
          date_of_birth: '',
          is_certified: false
        };

        await this.loadVolunteers(this.selectedAssociation.id);
        this.showToast('✅ Volontario aggiunto', 'success');
      } catch (error) {
        this.showToast('Errore: ' + error.message, 'error');
      }
    },

    async deleteVolunteer(volunteerId) {
      if (confirm('Sei sicuro di voler eliminare questo volontario?')) {
        try {
          await this.apiCall(`/associations/${this.selectedAssociation.id}/volunteers/${volunteerId}`, {
            method: 'DELETE'
          });

          await this.loadVolunteers(this.selectedAssociation.id);
          this.showToast('✅ Volontario eliminato', 'success');
        } catch (error) {
          this.showToast('Errore: ' + error.message, 'error');
        }
      }
    },

    // Utility functions
    showToast(message, type = 'info') {
      this.$dispatch('notify', { variant: type, message: message })
    },

    validateForm(formData, rules) {
      const errors = [];

      for (const [field, fieldRules] of Object.entries(rules)) {
        const value = formData[field];

        if (fieldRules.required && (!value || value.trim() === '')) {
          errors.push(`${fieldRules.label} è obbligatorio`);
          continue;
        }

        if (value && fieldRules.minLength && value.length < fieldRules.minLength) {
          errors.push(`${fieldRules.label} deve essere di almeno ${fieldRules.minLength} caratteri`);
        }

        if (value && fieldRules.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          errors.push(`${fieldRules.label} deve essere un indirizzo email valido`);
        }

        if (value && fieldRules.pattern && !fieldRules.pattern.test(value)) {
          errors.push(fieldRules.message || `${fieldRules.label} non è valido`);
        }
      }

      return errors;
    },

    debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },

    // Role-based access control helpers
    canAdmin() {
      return this.user && (this.user.role === 'admin' || this.user.role === 'superadmin');
    },

    canSuperAdmin() {
      return this.user && this.user.role === 'superadmin';
    },

    canViewOnly() {
      return this.user && this.user.role === 'viewer';
    },

    formatDate(dateString) {
      if (!dateString) return '';
      return new Date(dateString).toLocaleDateString('it-IT', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    formatDateTimeLocal(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    },

    formatCurrency(amount) {
      if (amount == null) return '€ 0,00';
      return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
      }).format(amount);
    },

    getStatusOptions() {
      return [
        { value: 'To Be Scheduled', label: 'Da programmare' },
        { value: 'Contribution Received', label: 'Contributo ricevuto' },
        { value: 'Certified Assembly', label: 'Montaggio certificato' },
        { value: 'Contribution Paid to Association', label: 'Contributo pagato all\'associazione' },
        { value: 'Completed', label: 'Completato' }
      ];
    },

    getStatusClass(status) {
      const classes = {
        'To Be Scheduled': 'bg-gray-100 text-gray-800',
        'Contribution Received': 'bg-blue-100 text-blue-800',
        'Certified Assembly': 'bg-yellow-100 text-yellow-800',
        'Contribution Paid to Association': 'bg-purple-100 text-purple-800',
        'Completed': 'bg-green-100 text-green-800'
      };

      return classes[status] || 'bg-gray-100 text-gray-800';
    },

    getStatusText(status) {
      const labels = {
        'To Be Scheduled': 'Da programmare',
        'Contribution Received': 'Contributo ricevuto',
        'Certified Assembly': 'Montaggio certificato',
        'Contribution Paid to Association': 'Contributo pagato all\'associazione',
        'Completed': 'Completato'
      };

      return labels[status] || status;
    },

    // Navigation and URL handling
    handleUrlFragment() {
      const hash = window.location.hash.slice(1); // Remove #
      if (hash && this.primaryMenu.some(item => item.route === hash)) {
        this.navigateToPage(hash, false); // Don't update URL again
      }
    },

    navigateToPage(page, updateUrl = true) {
      this.currentPage = page;
      if (updateUrl) {
        window.location.hash = page;
      }
      
      // Refresh data when changing pages
      this.refreshCurrentPageData();
    },

    async refreshCurrentPageData() {
      try {
        if (!this.isAuthenticated) return;
        
        switch (this.currentPage) {
          case 'events':
            await this.loadEvents();
            break;
          case 'associations':
            await this.loadAssociations();
            break;
          case 'reports':
            await this.loadReports();
            break;
          case 'dashboard':
            await this.loadInitialData();
            break;
        }
      } catch (error) {
        console.warn('Error refreshing page data:', error);
      }
    },

    async refreshData() {
      this.showToast('🔄 Aggiornamento dati...', 'info');
      await this.refreshCurrentPageData();
      this.showToast('✅ Dati aggiornati', 'success');
    },

    async downloadEventsCSV() {
      try {
        const params = new URLSearchParams();
        if (this.eventFilters.status) {
          params.append('status', this.eventFilters.status);
        }
        
        const response = await fetch(this.apiUrl + '/events/export/csv?' + params.toString(), {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Errore durante il download del CSV');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'eventi.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        this.showToast('✅ CSV scaricato con successo', 'success');
      } catch (error) {
        this.showToast('Errore nel download del CSV: ' + error.message, 'error');
      }
    }
  }))
});
