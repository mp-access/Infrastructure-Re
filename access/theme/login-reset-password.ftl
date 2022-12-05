<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="robots" content="noindex, nofollow">
  <title>ACCESS</title>
  <link rel="icon" href="${url.resourcesPath}/img/favicon.ico" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Courier+Prime&family=DM+Sans:wght@400;700&family=Manrope:wght@400;600&display=swap">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" crossorigin>
  <link rel="stylesheet" href="${url.resourcesPath}/css/login.css" />
</head>
<body class="d-flex flex-column align-items-center gap-5">
<div class="d-flex flex-row w-100 py-3 px-5 bg-white">
  <h1 class="m-0" style="font-family: 'Courier Prime', monospace">ACCESS.</h1>
</div>
<div class="d-flex flex-row align-items-center h-75 gap-5">
  <div class="d-flex flex-column align-items-center gap-4">
    <div class="d-flex flex-column align-items-center">
    <h1 style="font-family: 'DM Sans', sans-serif;font-weight: bold">Welcome to ACCESS!</h1>
    <text>...or did you forget your password?</text>
    </div>
    <img src="${url.resourcesPath}/img/robot.svg" width="60" height="100" alt="robot" style="width: 10rem; height: 10rem" />
  </div>
  <div class="d-flex flex-column align-items-center p-5 bg-white gap-3" style="border-radius: 1.5rem;position: relative;">
    <h3 style="font-family: 'DM Sans', sans-serif;font-weight: bold">Set your password</h3>
    <#if message?has_content>
      <div class="alert alert-danger" style="position: absolute;top: -5rem;" role="alert">
        <text>Invalid username or password.</text>
      </div>
    </#if>
    <form onsubmit="return true;" action="${url.loginAction}" method="post">
      <div class="mb-3">
        <label for="username" class="form-label small">Email</label>
        <div class="input-group">
          <input tabindex="0" required id="username" class="form-control py-2" name="username" value="${(login.username!'')}" type="text" autoComplete="new-password">
          <i class="bi bi-person input-group-text"></i>
        </div>
      </div>
      <div class="mb-5">
        <label for="password" class="form-label small">Password</label>
        <div class="input-group">
          <input tabindex="0" required id="password" class="form-control py-2" name="password" type="password" autoComplete="new-password">
          <i class="bi bi-key input-group-text"></i>
        </div>
      </div>
      <button tabindex="0" type="submit" class="btn btn-lg btn-primary w-100 border-0">
        Submit
      </button>
    </form>
  </div>
</div>
</body>
</html>