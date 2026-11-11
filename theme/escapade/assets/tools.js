/* Outils Escapade et Voyage : budget, partage des dépenses, décalage horaire, bagages, trajet en voiture.
   Aucune dépendance, aucun envoi de données : tout se calcule dans le navigateur. */
(function () {
  'use strict';

  function parse(v) { var n = parseFloat(String(v || '').replace(/\s/g, '').replace(',', '.')); return isNaN(n) ? null : n; }
  function num(form, name) { var el = form.elements[name]; return el ? parse(el.value) : null; }
  function fmt(n, d) { return Number(n).toLocaleString('fr-FR', { maximumFractionDigits: d || 0, minimumFractionDigits: d || 0 }); }
  function eur(n) { return fmt(Math.round(n * 100) / 100, Math.abs(n % 1) > 0.004 ? 2 : 0) + ' €'; }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function error(box, msg) { box.innerHTML = '<p class="gc-error">' + esc(msg) + '</p>'; }

  /* ---------------------------------------------------------------- Budget */
  function budget(form, box) {
    var jours = num(form, 'jours'), n = num(form, 'voyageurs') || 1;
    if (!jours || jours < 1) return error(box, 'Indiquez la durée du voyage en jours.');
    var nuits = Math.max(jours - 1, 1), postes = [], total = 0;
    Array.prototype.forEach.call(form.querySelectorAll('input[data-period]'), function (el) {
      var v = parse(el.value) || 0, p = el.getAttribute('data-period');
      var t = p === 'night' ? v * nuits : p === 'day' ? v * jours : v;
      if (t) { postes.push([el.closest('.gc-field').querySelector('label').textContent.replace(/\s*\(.*\)$/, ''), t]); total += t; }
    });
    if (!total) return error(box, 'Saisissez au moins un montant.');
    var marge = (parseInt(form.elements.marge.value, 10) || 0) / 100, avec = total * (1 + marge);
    postes.sort(function (a, b) { return b[1] - a[1]; });
    var rows = postes.map(function (p) {
      return '<tr><td>' + esc(p[0]) + '</td><td>' + eur(p[1]) + '</td><td>' + fmt(100 * p[1] / total) + ' %</td></tr>';
    }).join('');
    var sur = (total - (postes.filter(function (p) { return /Billets|Assurance/.test(p[0]); }).reduce(function (s, p) { return s + p[1]; }, 0))) / jours / n;
    box.innerHTML = '<p class="gc-big">' + eur(avec) + ' au total' + (marge ? ', marge de ' + fmt(marge * 100) + ' % comprise' : '') + '</p>'
      + '<p class="gc-big">' + eur(avec / n) + ' par personne, soit ' + eur(avec / n / jours) + ' par jour</p>'
      + '<p>Sur place, hors billets et assurance : <strong>' + eur(sur) + ' par personne et par jour</strong>. C\'est le chiffre à comparer d\'une destination à l\'autre.</p>'
      + '<table class="gc-table"><thead><tr><th>Poste</th><th>Montant</th><th>Part</th></tr></thead><tbody>' + rows + '</tbody></table>'
      + '<p class="gc-note">Hébergement compté sur ' + nuits + ' nuit' + (nuits > 1 ? 's' : '') + ', repas et transports sur ' + jours + ' jours. '
      + 'Le premier poste est souvent celui où l\'on gagne le plus : logement chez l\'habitant, auberge, ou étape un peu à l\'écart des quartiers touristiques.</p>';
  }

  /* -------------------------------------------------------------- Dépenses */
  function depenses(form, box) {
    var lignes = String(form.elements.lignes.value || '').split(/\r?\n/).map(function (l) { return l.trim(); }).filter(Boolean);
    if (!lignes.length) return error(box, 'Ajoutez au moins une dépense : qui a payé ; montant ; pour qui.');
    var gens = {}, achats = [], ignorees = 0;
    lignes.forEach(function (l) {
      var p = l.split(/;|\t/).map(function (x) { return x.trim(); });
      var payeur = p[0], m = parse(p[1]);
      if (!payeur || m === null || m <= 0) { ignorees++; return; }
      gens[payeur] = gens[payeur] || 0;
      var pour = (p[2] || 'tous').toLowerCase() === 'tous' ? null : p[2].split(/,|\bet\b/).map(function (x) { return x.trim(); }).filter(Boolean);
      if (pour) pour.forEach(function (x) { gens[x] = gens[x] || 0; });
      achats.push({ payeur: payeur, m: m, pour: pour });
    });
    var noms = Object.keys(gens);
    if (!achats.length || noms.length < 2) return error(box, 'Il faut au moins deux participants.');
    var solde = {}, total = 0, part = {};
    noms.forEach(function (x) { solde[x] = 0; part[x] = 0; });
    achats.forEach(function (a) {
      var cible = a.pour || noms;
      solde[a.payeur] += a.m; total += a.m;
      cible.forEach(function (x) { solde[x] -= a.m / cible.length; part[x] += a.m / cible.length; });
    });
    // Remboursements minimaux : le plus gros débiteur rembourse le plus gros créancier.
    var deb = noms.filter(function (x) { return solde[x] < -0.005; }).map(function (x) { return [x, -solde[x]]; });
    var cre = noms.filter(function (x) { return solde[x] > 0.005; }).map(function (x) { return [x, solde[x]]; });
    var virements = [];
    while (deb.length && cre.length) {
      deb.sort(function (a, b) { return b[1] - a[1]; }); cre.sort(function (a, b) { return b[1] - a[1]; });
      var v = Math.min(deb[0][1], cre[0][1]);
      virements.push(deb[0][0] + ' doit <strong>' + eur(v) + '</strong> à ' + cre[0][0]);
      deb[0][1] -= v; cre[0][1] -= v;
      if (deb[0][1] < 0.005) deb.shift();
      if (cre[0][1] < 0.005) cre.shift();
    }
    var tab = noms.map(function (x) {
      return '<tr><td>' + esc(x) + '</td><td>' + eur(part[x]) + '</td><td>' + (solde[x] >= 0 ? '+' : '') + eur(solde[x]) + '</td></tr>';
    }).join('');
    box.innerHTML = '<p class="gc-big">' + (virements.length ? virements.length + ' virement' + (virements.length > 1 ? 's' : '') + ' pour solder les comptes' : 'Les comptes sont déjà équilibrés') + '</p>'
      + (virements.length ? '<ul>' + virements.map(function (v) { return '<li>' + v.replace(/^([^<]+) doit/, function (m, a) { return esc(a) + ' doit'; }) + '</li>'; }).join('') + '</ul>' : '')
      + '<table class="gc-table"><thead><tr><th>Voyageur</th><th>Sa part</th><th>Solde</th></tr></thead><tbody>' + tab + '</tbody></table>'
      + '<p class="gc-note">Total des dépenses : ' + eur(total) + '. Un solde positif signifie que la personne a avancé plus que sa part.'
      + (ignorees ? ' ' + ignorees + ' ligne(s) ignorée(s) : montant illisible.' : '') + '</p>';
  }

  /* -------------------------------------------------------------- Décalage */
  function offsetMinutes(zone, date) {
    var parts = new Intl.DateTimeFormat('en-US', { timeZone: zone, hourCycle: 'h23', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric' }).formatToParts(date);
    var o = {}; parts.forEach(function (p) { o[p.type] = +p.value; });
    return (Date.UTC(o.year, o.month - 1, o.day, o.hour % 24, o.minute) - Math.floor(date.getTime() / 60000) * 60000) / 60000;
  }
  function decalage(form, box) {
    var dep = form.elements.depart.value, dst = form.elements.dest.value;
    var d = form.elements.date.value ? new Date(form.elements.date.value + 'T12:00:00Z') : new Date();
    var diff = offsetMinutes(dst, d) - offsetMinutes(dep, d), h = diff / 60;
    var abs = Math.abs(h), dh = Math.floor(abs), dm = Math.round((abs - dh) * 60);
    var txt = (dh ? dh + ' h' : '') + (dm ? (dh ? ' ' : '') + dm + ' min' : '') || '0 h';
    var nomD = form.elements.dest.options[form.elements.dest.selectedIndex].text, nomP = form.elements.depart.options[form.elements.depart.selectedIndex].text;
    var local = new Intl.DateTimeFormat('fr-FR', { timeZone: dst, hour: '2-digit', minute: '2-digit' }).format(new Date());
    var html;
    if (!diff) {
      html = '<p class="gc-big">Pas de décalage horaire à cette date</p>';
    } else {
      var est = h > 0;
      html = '<p class="gc-big">' + esc(nomD) + ' : ' + (est ? '+' : '−') + txt + ' par rapport à ' + esc(nomP) + '</p>'
        + '<p>Il est actuellement <strong>' + local + '</strong> à destination.</p>';
      if (abs >= 3) {
        var jours = Math.round(abs / (est ? 1 : 1.5));
        html += '<p>Vers ' + (est ? 'l\'est, on « perd » des heures : c\'est le sens le plus difficile.' : 'l\'ouest, on « gagne » des heures : la journée s\'allonge, l\'adaptation est plus facile.')
          + ' Comptez <strong>environ ' + jours + ' jour' + (jours > 1 ? 's' : '') + '</strong> pour être tout à fait calé, à raison d\'une heure par jour ' + (est ? '' : 'à une heure et demie ') + 'en moyenne.</p>'
          + '<ul><li>Les ' + (abs >= 6 ? '3' : '2') + ' jours avant le départ, ' + (est ? 'couchez-vous et levez-vous une heure plus tôt chaque jour.' : 'décalez votre coucher d\'une heure plus tard chaque jour.') + '</li>'
          + '<li>À l\'arrivée, vivez tout de suite à l\'heure locale : repas, coucher, et surtout lumière du jour ' + (est ? 'le matin' : 'en fin de journée') + '.</li>'
          + '<li>Une sieste de 20 minutes au plus, avant 15 h locales.</li>'
          + '<li>Pour un séjour de moins de trois jours, il est souvent plus simple de rester calé sur l\'heure de départ.</li></ul>';
      } else {
        html += '<p>Moins de trois heures d\'écart : la plupart des voyageurs s\'adaptent en un à deux jours, sans préparation particulière.</p>';
      }
    }
    html += '<p class="gc-note">Calcul fait avec la base des fuseaux horaires de votre navigateur, heure d\'été comprise à la date choisie. Repères de récupération : environ une journée par heure de décalage vers l\'est, un peu moins vers l\'ouest (Centers for Disease Control and Prevention, Yellow Book).</p>';
    box.innerHTML = html;
  }

  /* --------------------------------------------------------------- Bagages */
  function bagages(form, box) {
    var j = num(form, 'jours') || 7, c = form.elements.climat.value, st = form.elements.style.value, sac = form.elements.sac.value;
    var horsUe = form.elements.hors_ue.checked, enfants = form.elements.enfants.checked, travail = form.elements.travail.checked;
    var lessive = j > 7 ? 7 : j, n = function (k) { return Math.max(1, Math.ceil(lessive * k)); };
    var L = {
      'Papiers et argent': ['Carte d\'identité ou passeport en cours de validité', 'Carte bancaire (et une seconde, rangée ailleurs)', 'Un peu d\'espèces de secours', 'Attestation d\'assurance voyage', 'Copie numérique des papiers, envoyée à vous-même'],
      'Vêtements': [n(1) + ' tenues de base (hauts)', n(0.5) + ' bas (pantalons, jupes, shorts)', n(1) + ' sous-vêtements et paires de chaussettes', 'Une tenue un peu habillée', 'Chaussures confortables déjà portées'],
      'Toilette et santé': ['Trousse de toilette (flacons de 100 ml maximum en cabine)', 'Médicaments habituels, avec l\'ordonnance', 'Pansements, antiseptique, antidouleur', 'Crème solaire'],
      'Électronique': ['Téléphone et chargeur', 'Batterie externe (en cabine, jamais en soute)', 'Écouteurs'],
      'Confort': ['Gourde', 'Sac pliable pour la journée', 'Bouchons d\'oreilles et masque de nuit']
    };
    if (c === 'chaud' || c === 'tropical') L['Vêtements'].push('Chapeau ou casquette', 'Lunettes de soleil', 'Maillot de bain');
    if (c === 'tropical') { L['Toilette et santé'].push('Répulsif anti-moustiques adapté à la zone', 'Sels de réhydratation'); L['Vêtements'].push('Vêtements longs et légers pour le soir', 'Petit imperméable'); }
    if (c === 'froid') L['Vêtements'].push('Doudoune légère ou polaire', 'Bonnet, gants, écharpe', 'Sous-couche thermique', 'Chaussures imperméables');
    if (c === 'tempere') L['Vêtements'].push('Un pull', 'Un coupe-vent imperméable');
    if (st === 'nature') { L['Vêtements'].push('Chaussures de randonnée', 'Vêtements techniques qui sèchent vite'); L['Confort'].push('Frontale', 'Carte hors ligne téléchargée sur le téléphone'); }
    if (st === 'plage') L['Confort'].push('Serviette de plage légère', 'Masque et tuba', 'Sac étanche pour le téléphone');
    if (st === 'ville') L['Confort'].push('Plans hors ligne des villes', 'Petit cadenas pour le sac');
    if (st === 'route') { L['Papiers et argent'].push('Permis de conduire (et permis international si exigé)', 'Carte grise et attestation d\'assurance du véhicule'); L['Confort'].push('Support et câble pour téléphone en voiture', 'Glacière souple'); }
    if (horsUe) { L['Papiers et argent'][0] = 'Passeport, valide encore au moins six mois après le retour (exigence fréquente hors UE)'; L['Papiers et argent'].push('Visa ou autorisation électronique si le pays l\'exige', 'Carte européenne d\'assurance maladie : inutile hors UE, vérifiez votre assurance'); L['Électronique'].push('Adaptateur de prise'); }
    else L['Papiers et argent'].push('Carte européenne d\'assurance maladie');
    if (enfants) { L['Papiers et argent'].push('Papiers d\'identité de chaque enfant (et autorisation de sortie du territoire si besoin)'); L['Confort'].push('Doudou, jeux et livres pour le trajet', 'En-cas pour les attentes'); L['Toilette et santé'].push('Thermomètre et médicaments enfants'); }
    if (travail) L['Électronique'].push('Ordinateur et chargeur', 'Multiprise de voyage', 'Partage de connexion ou carte SIM / eSIM locale');
    if (sac === 'cabine') L['Toilette et santé'].unshift('Liquides en flacons de 100 ml, dans un sachet transparent de 1 litre');
    var html = '<p class="gc-big">Votre liste pour ' + j + ' jour' + (j > 1 ? 's' : '') + '</p>';
    if (j > 7) html += '<p>Au-delà d\'une semaine, la liste prévoit des vêtements pour 7 jours et une lessive sur place : c\'est ce qui permet de voyager léger.</p>';
    Object.keys(L).forEach(function (k) {
      html += '<p class="gc-list-title"><strong>' + k + '</strong></p><ul class="gc-checklist">' + L[k].map(function (x, i) {
        return '<li><label><input type="checkbox"> ' + esc(x) + '</label></li>';
      }).join('') + '</ul>';
    });
    html += '<p><button type="button" class="btn btn-ghost gc-print">Imprimer la liste</button></p>'
      + '<p class="gc-note">Formalités, vaccins et conseils de sécurité : vérifiez toujours la fiche du pays sur France Diplomatie avant de partir.</p>';
    box.innerHTML = html;
  }

  /* ---------------------------------------------------------------- Trajet */
  function trajet(form, box) {
    var km = num(form, 'km'), ar = parseInt(form.elements.ar.value, 10), conso = num(form, 'conso'), prix = num(form, 'prix');
    if (!km || !conso || !prix) return error(box, 'Indiquez la distance, la consommation et le prix du carburant ou de l\'électricité.');
    var dist = km * ar, energie = dist * conso / 100 * prix, peages = (num(form, 'peages') || 0) * ar;
    var p = num(form, 'personnes') || 1, total = energie + peages;
    var html = '<p class="gc-big">' + eur(total) + ' pour ' + fmt(dist) + ' km</p>'
      + '<p>Carburant ou recharge : ' + eur(energie) + (peages ? ' · péages : ' + eur(peages) : '') + '</p>'
      + '<p class="gc-big">' + eur(total / p) + ' par personne</p>';
    var t = num(form, 'train');
    if (t) {
      var tTotal = t * p * ar;
      html += '<p>En train ou en avion, au même tarif pour ' + p + ' personne' + (p > 1 ? 's' : '') + ' : <strong>' + eur(tTotal) + '</strong>. '
        + (tTotal > total ? 'La voiture revient ' + eur(tTotal - total) + ' moins cher' : 'Le train ou l\'avion revient ' + eur(total - tTotal) + ' moins cher') + ', sans compter le stationnement à destination ni l\'usure du véhicule.</p>';
    }
    html += '<p class="gc-note">Coût direct seulement. Le barème kilométrique fiscal, qui inclut l\'entretien et la dépréciation, donne un coût complet nettement plus élevé.</p>';
    box.innerHTML = html;
  }

  var HANDLERS = { budget: budget, depenses: depenses, decalage: decalage, bagages: bagages, trajet: trajet };

  document.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('.gc-print')) window.print();
  });
  document.querySelectorAll('.gc-tool').forEach(function (tool) {
    var id = tool.getAttribute('data-tool'), form = tool.querySelector('form'), box = tool.querySelector('.gc-tool-result');
    if (!HANDLERS[id] || !form || !box) return;
    if (id === 'decalage' && form.elements.date && !form.elements.date.value) form.elements.date.value = new Date().toISOString().slice(0, 10);
    form.addEventListener('submit', function (e) { e.preventDefault(); HANDLERS[id](form, box); });
  });
})();
