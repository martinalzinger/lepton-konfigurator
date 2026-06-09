<?php
/* Zentrale Datenhaltung für das Alzinger Vertriebs-CRM (geteilt).
   - Single-File, dateibasiert: Daten in ./data/crm.json (kein DB-Server nötig).
   - Drop-in: diese Datei + index.html etc. in einen Web-Ordner mit PHP legen
     (IIS+PHP, Apache, nginx+php-fpm, Synology/QNAP …) und im Browser aufrufen.
   - Der Ordner ./data muss vom Webserver beschreibbar sein.
   Optionaler Zugriffsschutz: $TOKEN setzen und denselben Wert in der App
   (Reiter „Daten“ → Zugriffsschutz) hinterlegen. */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

$TOKEN = '';   // leer = kein Schutz. Sonst geheimer Wert, identisch in der App.

if ($TOKEN !== '') {
  $sent = isset($_SERVER['HTTP_X_CRM_TOKEN']) ? $_SERVER['HTTP_X_CRM_TOKEN']
        : (isset($_GET['token']) ? $_GET['token'] : '');
  if (!hash_equals($TOKEN, (string)$sent)) {
    http_response_code(401); echo json_encode(array('error'=>'unauthorized')); exit;
  }
}

$DIR  = __DIR__ . '/data';
$FILE = $DIR . '/crm.json';
if (!is_dir($DIR)) @mkdir($DIR, 0775, true);

function read_db($FILE){
  if (!file_exists($FILE)) return array('rev'=>0,'contacts'=>array());
  $d = json_decode((string)file_get_contents($FILE), true);
  if (!is_array($d)) $d = array();
  if (!isset($d['contacts']) || !is_array($d['contacts'])) $d['contacts'] = array();
  if (!isset($d['rev'])) $d['rev'] = 0;
  return $d;
}
function write_db($FILE,$d){
  $tmp = $FILE . '.tmp';
  file_put_contents($tmp, json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));
  @rename($tmp, $FILE);
}
function reindex($db){ $i=array(); foreach($db['contacts'] as $k=>$c){ if(isset($c['id'])) $i[$c['id']]=$k; } return $i; }

$action = isset($_GET['action']) ? $_GET['action'] : '';
$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET' && ($action === 'all' || $action === '')) {
  echo json_encode(read_db($FILE), JSON_UNESCAPED_UNICODE); exit;
}

if ($method === 'POST' && $action === 'batch') {
  $body = json_decode((string)file_get_contents('php://input'), true);
  $ops  = (isset($body['ops']) && is_array($body['ops'])) ? $body['ops'] : array();

  $lf = fopen($FILE.'.lock','c');                 // exklusive Sperre über Lesen-Ändern-Schreiben
  if ($lf) flock($lf, LOCK_EX);
  $db  = read_db($FILE);
  $idx = reindex($db);
  foreach ($ops as $op) {
    $type = isset($op['op']) ? $op['op'] : '';
    if ($type === 'upsert' && isset($op['contact']['id'])) {
      $c = $op['contact']; $id = $c['id'];
      if (isset($idx[$id])) $db['contacts'][$idx[$id]] = $c;
      else { $idx[$id] = count($db['contacts']); $db['contacts'][] = $c; }
    } else if ($type === 'delete' && isset($op['id'])) {
      $id = $op['id'];
      if (isset($idx[$id])) { array_splice($db['contacts'], $idx[$id], 1); $idx = reindex($db); }
    } else if ($type === 'bulk') {
      $list = (isset($op['contacts']) && is_array($op['contacts'])) ? $op['contacts'] : array();
      if (!empty($op['replace'])) { $db['contacts'] = $list; $idx = reindex($db); }
      else {
        foreach ($list as $c) {
          if (!isset($c['id'])) continue; $id = $c['id'];
          if (isset($idx[$id])) $db['contacts'][$idx[$id]] = $c;
          else { $idx[$id] = count($db['contacts']); $db['contacts'][] = $c; }
        }
      }
    }
  }
  $db['rev'] = intval($db['rev']) + 1;
  write_db($FILE, $db);
  if ($lf) { flock($lf, LOCK_UN); fclose($lf); }
  echo json_encode(array('ok'=>true,'rev'=>$db['rev'],'count'=>count($db['contacts']))); exit;
}

http_response_code(400);
echo json_encode(array('error'=>'bad request'));
