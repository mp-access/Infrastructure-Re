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
<body>
<div class="blob-container" style="background-image:url(${url.resourcesPath}/img/blob.svg);background-position: -20vw 80vh;z-index: -1">
</div>
<div class="blob-container" style="background-image:url(${url.resourcesPath}/img/blob.svg);background-position: 60vw -30vh;z-index: -1">
</div>
<div class="d-flex flex-column align-items-center gap-5 p-5">
  <div class="d-flex w-100">
    <h1 class="m-0" style="font-family: 'Courier Prime', monospace; font-size: 3rem;">ACCESS.</h1>
  </div>
  <div class="d-flex justify-content-center w-100 align-items-center">
    <div style="max-width: 40vw;">
      <img src="${url.resourcesPath}/img/programming.svg" width="100" height="100" alt="rocket" style="width: 100%; height: 100%" />
    </div>
    <div class="align-items-center d-flex flex-column gap-3 mx-5" style="min-width:max-content;position: relative;">
      <div class="d-flex gap-2 mb-2">
        <h3 style="font-weight: bold;">Sign in to</h3>
        <h3 style="font-weight: bold;color: #0085ff;">My ACCESS</h3>
      </div>
        <#if message?has_content>
          <div class="alert alert-danger" style="position: absolute;top: -5rem;" role="alert">
            <text>Invalid username or password.</text>
          </div>
        </#if>
      <div class="align-items-center d-flex flex-column gap-2 w-100">
        <text>Log in with your organization</text>
        <#if social.providers??>
            <#list social.providers as p>
                <#if p.displayName = "SWITCH-AAI">
                  <button tabindex="0" class="btn btn-lg btn-light py-3 border-0 w-100" onclick="location.href='${p.loginUrl}';">
                    <img src="${url.resourcesPath}/img/switch_aai.svg" width="100" height="18" alt="rocket" />
                  </button>
                </#if>
            </#list>
        </#if>
      </div>
      <div class="border-bottom my-3 w-100" style="position: relative;height: 0.8rem;">
        <text class="px-2" style="font-size: 0.8rem;position: absolute;top: 20%;left: 45%;background: white;">or</text>
      </div>
      <form class="w-100" onsubmit="return true;" action="${url.loginAction}" method="post">
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
        <div class="justify-content-center d-flex w-100">
          <button tabindex="0" name="login" type="submit" class="border-0 btn btn-lg btn-primary px-5">
            Sign in
          </button>
        </div>
      </form>
      <#if realm.resetPasswordAllowed>
        <button tabindex="0" class="btn btn-info btn-sm border-0" onclick="location.href='${url.loginResetCredentialsUrl}';">
          Forgot password?
        </button>
      </#if>
    </div>
  </div>
</div>
</body>
</html>