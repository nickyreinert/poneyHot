document.addEventListener('DOMContentLoaded', function() {
  console.log('Popup script loaded');
  
  // Load existing backend domain setting
  browser.storage.local.get('backendDomain').then(result => {
      const domainInput = document.getElementById('domain-input');
      if (result.backendDomain) {
          domainInput.value = result.backendDomain;
      } else {
          // Set default value if none exists
          domainInput.value = 'http://localhost:8080';
      }
  });

  // Save backend domain setting
  document.getElementById('save-domain').addEventListener('click', () => {
      const domainInput = document.getElementById('domain-input');
      let domain = domainInput.value.trim();
      
      // Add http:// if no protocol specified
      if (!domain.startsWith('http://') && !domain.startsWith('https://')) {
          domain = 'http://' + domain;
      }

      // Basic URL validation
      try {
          new URL(domain);
          browser.storage.local.set({ backendDomain: domain });
          alert('Domain saved successfully!');
      } catch (e) {
          alert('Please enter a valid domain');
      }
  });
});