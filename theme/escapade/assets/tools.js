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
  // Base : theme/escapade/assets/budget-data.json (niveau des prix Banque mondiale + modèle + articles).
  var BUDGET = null;
  var POSTES = { logement: 'Hébergement', repas: 'Repas', transports: 'Transports sur place', activites: 'Visites et activités', divers: 'Divers' };
  var SAISONS = { printemps: [3, 4, 5], ete: [6, 7, 8], automne: [9, 10, 11], hiver: [12, 1, 2] };
  function round5(n) { return Math.max(5, Math.round(n / 5) * 5); }
  function saisonDe(dest, cle) {
    var m = SAISONS[cle], h = m.filter(function (x) { return dest.haute.indexOf(x) > -1; }).length, b = m.filter(function (x) { return dest.basse.indexOf(x) > -1; }).length;
    return h >= 2 ? 'haute' : b >= 2 ? 'basse' : 'moyenne';
  }
  function niveau(B, dest, opts, palier) {
    var base = B.modele[palier], el = B.elasticite, co = B.coefficients, r = dest.ratio;
    var sa = co.saison[opts.saison] || {}, st = co.style[opts.style] || {}, enf = co.enfant;
    var parAdulte = {}, groupe = {};
    Object.keys(POSTES).forEach(function (k) {
      var e = (k === 'logement' && palier === 'gros') ? el.gros_logement : el[k];
      var v = base[k] * Math.pow(r, e) * (sa[k] || 1) * (st[k] || 1);
      parAdulte[k] = v;
      var adultes = opts.adultes * v;
      if (k === 'logement' && opts.adultes === 1) adultes = v * co.solo_logement;
      groupe[k] = (adultes + opts.enfants * v * (enf[k] || 1)) * opts.jours;
    });
    var jourAdulte = Object.keys(parAdulte).reduce(function (s, k) { return s + parAdulte[k]; }, 0);
    // Un budget relevé dans un de nos articles remplace l'estimation, en gardant la répartition par poste.
    var art = dest.article, source = 'modele';
    if (art && art[palier]) {
      var f = art[palier] / jourAdulte;
      Object.keys(groupe).forEach(function (k) { groupe[k] *= f; });
      jourAdulte = art[palier]; source = 'article';
    }
    var total = Object.keys(groupe).reduce(function (s, k) { return s + groupe[k]; }, 0);
    return { jour: jourAdulte, total: total, postes: groupe, source: source };
  }
  function renderBudget(B, form, box) {
    var iso = form.elements.dest.value;
    var dest = B.destinations.filter(function (d) { return d.pays === iso; })[0];
    if (!dest) return error(box, 'Choisissez une destination.');
    var opts = {
      jours: Math.max(1, Math.round(num(form, 'jours') || 10)), adultes: Math.max(1, Math.round(num(form, 'adultes') || 1)),
      enfants: Math.max(0, Math.round(num(form, 'enfants') || 0)), style: form.elements.style.value,
      saison: saisonDe(dest, form.elements.saison.value)
    };
    var nomSaison = { haute: 'haute saison', moyenne: 'saison intermédiaire', basse: 'basse saison' }[opts.saison];
    var qui = opts.adultes + ' adulte' + (opts.adultes > 1 ? 's' : '') + (opts.enfants ? ' et ' + opts.enfants + ' enfant' + (opts.enfants > 1 ? 's' : '') : '');
    var cartes = ['petit', 'moyen', 'gros'].map(function (p) {
      var n = niveau(B, dest, opts, p);
      var lignes = Object.keys(POSTES).map(function (k) { return '<tr><td>' + POSTES[k] + '</td><td>' + eur(round5(n.postes[k])) + '</td></tr>'; }).join('');
      return '<div class="ev-budget-card ev-budget-' + p + '"><p class="ev-budget-tier">' + { petit: 'Petit budget', moyen: 'Budget moyen', gros: 'Grand confort' }[p] + '</p>'
        + '<p class="ev-budget-total">' + eur(round5(n.total)) + '</p>'
        + '<p class="ev-budget-day">soit environ ' + eur(round5(n.jour)) + ' par adulte et par jour</p>'
        + '<p class="ev-budget-desc">' + esc(B.modele.libelles[p]) + '</p>'
        + '<details><summary>Détail par poste</summary><table class="gc-table"><tbody>' + lignes + '</tbody></table></details>'
        + (n.source === 'article' ? '<p class="ev-budget-src">Montant relevé dans notre article</p>' : '') + '</div>';
    }).join('');
    var r = dest.ratio, comp = r >= 0.95 && r <= 1.05 ? 'proches de ceux de la France' : (r < 1 ? 'environ ' + fmt(Math.round((1 - r) * 100)) + ' % moins élevés qu\'en France' : 'environ ' + fmt(Math.round((r - 1) * 100)) + ' % plus élevés qu\'en France');
    var art = dest.article ? '<p>Nos montants pour ce pays viennent de notre article <a href="' + esc(dest.article.url) + '">' + esc(dest.article.titre) + '</a>' + (dest.article.date ? ', relevés en ' + esc(dest.article.date.slice(0, 7)) : '') + '.</p>' : '';
    box.innerHTML = '<p class="gc-big">' + esc(dest.nom) + ', ' + opts.jours + ' jours, ' + qui + '</p>'
      + '<p>Votre voyage tombe en <strong>' + nomSaison + '</strong>.' + (dest.pays === 'FR' ? '' : ' Les prix y sont en moyenne ' + comp + ' (Banque mondiale, ' + dest.annee + ').') + '</p>'
      + '<div class="ev-budget-grid">' + cartes + '</div>' + art
      + '<p class="gc-note">Estimation hors billets pour rejoindre la destination. Moyennes nationales : les capitales et les stations très touristiques coûtent plus cher, les campagnes moins. '
      + 'Méthode : des budgets journaliers de référence en France, ajustés au niveau des prix du pays (Banque mondiale, parité de pouvoir d\'achat rapportée au taux de change), à la saison et à votre façon de voyager. Base mise à jour le ' + esc(B.maj.split('-').reverse().join('/')) + '.</p>';
  }
  function budget(form, box) {
    if (BUDGET) return renderBudget(BUDGET, form, box);
    var src = form.closest('.gc-tool').getAttribute('data-src');
    box.innerHTML = '<p class="gc-note">Chargement des données…</p>';
    fetch(src).then(function (r) { return r.json(); }).then(function (d) { BUDGET = d; renderBudget(d, form, box); })
      .catch(function () { error(box, 'Impossible de charger les données. Réessayez dans un instant.'); });
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
