# cletus\_mccoy\.android\_adb Release Notes

**Topics**

- <a href="#v0-6-0">v0\.6\.0</a>
    - <a href="#minor-changes">Minor Changes</a>
    - <a href="#bugfixes">Bugfixes</a>
- <a href="#v0-5-0">v0\.5\.0</a>
    - <a href="#minor-changes-1">Minor Changes</a>
    - <a href="#bugfixes-1">Bugfixes</a>
- <a href="#v0-4-1">v0\.4\.1</a>
    - <a href="#bugfixes-2">Bugfixes</a>
- <a href="#v0-4-0">v0\.4\.0</a>
    - <a href="#minor-changes-2">Minor Changes</a>
    - <a href="#new-modules">New Modules</a>
- <a href="#v0-3-0">v0\.3\.0</a>
    - <a href="#minor-changes-3">Minor Changes</a>
    - <a href="#new-modules-1">New Modules</a>
- <a href="#v0-2-1">v0\.2\.1</a>
    - <a href="#bugfixes-3">Bugfixes</a>
- <a href="#v0-2-0">v0\.2\.0</a>
    - <a href="#release-summary">Release Summary</a>
    - <a href="#minor-changes-4">Minor Changes</a>
    - <a href="#new-modules-2">New Modules</a>
- <a href="#v0-1-0">v0\.1\.0</a>
    - <a href="#release-summary-1">Release Summary</a>
    - <a href="#new-plugins">New Plugins</a>
        - <a href="#connection">Connection</a>
        - <a href="#inventory">Inventory</a>
    - <a href="#new-modules-3">New Modules</a>

<a id="v0-6-0"></a>
## v0\.6\.0

<a id="minor-changes"></a>
### Minor Changes

* adb\_config\, adb\_device\_info\, adb\_device\_state\, adb\_packages \- now honour <code>adb\_path</code> instead of always using <code>adb</code> from <code>PATH</code>\.
* all modules \- every module now accepts <code>device</code>\, <code>adb\_path</code> and <code>adb\_server\_port</code>\, so <code>module\_defaults</code> for <code>group/cletus\_mccoy\.android\_adb\.adb</code> no longer fails with \"Unsupported parameters\" on modules that lacked one of them\. <code>adb\_connect</code> and <code>adb\_pair</code> take <code>adb\_path</code>/<code>adb\_server\_port</code> only\.
* collection \- <code>requires\_ansible</code> raised to <code>\>\=2\.16\.0</code>\, the oldest ansible\-core version that is tested\.

<a id="bugfixes"></a>
### Bugfixes

* adb connection plugin \- fix documentation schema errors \(<code>name</code> key\, author format\)\.
* adb\_config \- document the <code>settings\_\*</code> and <code>shell</code> actions and the <code>namespace</code>/<code>command</code> options\.
* adb\_logcat \- remove a duplicated documentation block\.
* collection \- fix the <code>repository</code> link on Galaxy and add <code>issues</code>/<code>documentation</code>/<code>homepage</code> links\.
* collection \- published tarballs no longer include previous release tarballs\, <code>\_\_pycache\_\_</code> or the local <code>tests/integration/integration\_config\.yml</code>\.
* modules \- correct <code>version\_added</code> values\; several modules claimed versions \(1\.0\.0 to 1\.4\.0\) that were never released\.

<a id="v0-5-0"></a>
## v0\.5\.0

<a id="minor-changes-1"></a>
### Minor Changes

* adb\_facts\, adb\_connect\, adb\_shell\, adb\_pair \- new <code>adb\_server\_port</code> option to use a dedicated ADB server per device\.
* adb\_pair \- new <code>retries</code>/<code>retry\_delay</code>/<code>timeout</code>\; an expired pairing dialog fails with <code>expired\=true</code> and an actionable message\.

<a id="bugfixes-1"></a>
### Bugfixes

* adb\_intent \- errors that <code>am</code> prints to stderr while exiting 0 are now reported as failures\.

<a id="v0-4-1"></a>
## v0\.4\.1

<a id="bugfixes-2"></a>
### Bugfixes

* app\_management role \- <code>bulk\_update</code> passes package/version to adb\_install so devices already at the target version report <code>changed\=false</code>\.
* policy\_management role \- rewritten onto valid\, idempotent module calls\; <code>remote\_wipe</code> now requires <code>policy\_confirm\_wipe\=true</code>\.

<a id="v0-4-0"></a>
## v0\.4\.0

<a id="minor-changes-2"></a>
### Minor Changes

* android\_probe role \- rebuilt on adb\_facts\; unreachable devices are skipped instead of failing the play\.
* module\_utils \- every adb call now has a finite timeout \(<code>AdbTimeout</code>\) and a hung ADB server is detected and restarted\.

<a id="new-modules"></a>
### New Modules

* cletus\_mccoy\.android\_adb\.adb\_facts \- Gather Ansible facts from an Android device over ADB

<a id="v0-3-0"></a>
## v0\.3\.0

<a id="minor-changes-3"></a>
### Minor Changes

* adb\_connect \- new <code>prune\_offline</code> option removes stale <code>offline</code> entries left behind by <code>adb root</code>/<code>tcpip</code>\.
* module\_utils \- shared <code>ui\.py</code> helpers plus <code>run\_adb\_binary</code> and <code>list\_devices</code>\.

<a id="new-modules-1"></a>
### New Modules

* cletus\_mccoy\.android\_adb\.adb\_app\_pref \- Set or remove a key in an Android app\'s shared\_prefs XML \(root\)
* cletus\_mccoy\.android\_adb\.adb\_root \- Restart adbd as root \(or non\-root\) and re\-establish the connection
* cletus\_mccoy\.android\_adb\.adb\_screencap \- Capture a screenshot from an Android device to the controller
* cletus\_mccoy\.android\_adb\.adb\_ui\_dump \- Dump the current UI view hierarchy from an Android device
* cletus\_mccoy\.android\_adb\.adb\_ui\_tap \- Tap a UI element by text/resource\-id\, or at raw coordinates

<a id="v0-2-1"></a>
## v0\.2\.1

<a id="bugfixes-3"></a>
### Bugfixes

* adb\_files\, adb\_shell \- add missing documentation that made Galaxy\'s import fail\.
* adb\_settings \- correct the Settings DB permission note for Android 16 \(<code>WRITE\_SETTINGS</code> is no longer granted to the shell\)\.
* android\_probe role \- restore the <code>probe\_include\_system\_apps</code> default\; bare runs failed with an undefined variable\.
* app\_management role \- drop the invalid <code>update</code> argument and support <code>\{apk\_path\, package\, version\}</code> items for idempotent installs\.

<a id="v0-2-0"></a>
## v0\.2\.0

<a id="release-summary"></a>
### Release Summary

First deployment\-ready release\. Most modules are now idempotent\.

<a id="minor-changes-4"></a>
### Minor Changes

* New roles adb\_bootstrap and android\_config\; settings\_management now uses adb\_settings instead of raw shell\.
* adb connection plugin \- timeouts\, retries and error wrapping\.
* adb\_config \- idempotent <code>set</code> and new <code>settings\_delete</code> action\.
* adb\_connect \- idempotent\; detects an existing connection and supports <code>state\=absent</code>\.
* adb\_devices inventory plugin \- implemented\; parses <code>adb devices \-l</code> and groups devices\.
* adb\_forward \- idempotent \(checks <code>forward \-\-list</code>\)\; supports <code>state\=absent</code>\.
* adb\_install \- idempotent via <code>package</code>/<code>version</code>\; skips the install when the version already matches\.
* adb\_intent \- implemented <code>am start</code>/<code>startservice</code>/<code>broadcast</code>\.
* adb\_reboot \- new <code>wait</code>/<code>wait\_timeout</code> options wait for <code>sys\.boot\_completed</code>\.
* adb\_uninstall \- idempotent\; checks <code>pm list packages</code> first\.

<a id="new-modules-2"></a>
### New Modules

* cletus\_mccoy\.android\_adb\.adb\_files \- Push or pull files to/from an Android device via ADB
* cletus\_mccoy\.android\_adb\.adb\_settings \- Manage Android Settings database values over ADB
* cletus\_mccoy\.android\_adb\.adb\_shell \- Run an arbitrary command on an Android device via ADB shell

<a id="v0-1-0"></a>
## v0\.1\.0

<a id="release-summary-1"></a>
### Release Summary

Initial release\.

<a id="new-plugins"></a>
### New Plugins

<a id="connection"></a>
#### Connection

* cletus\_mccoy\.android\_adb\.adb \- Execute Ansible tasks over Android Debug Bridge \(ADB\)

<a id="inventory"></a>
#### Inventory

* cletus\_mccoy\.android\_adb\.adb\_devices \- Inventory source for Android devices reachable via ADB

<a id="new-modules-3"></a>
### New Modules

* cletus\_mccoy\.android\_adb\.adb\_config \- Manage Android device configuration over ADB
* cletus\_mccoy\.android\_adb\.adb\_connect \- Connect to \(or disconnect from\) an Android device over ADB \(wireless\)
* cletus\_mccoy\.android\_adb\.adb\_device\_info \- Gather Android device info over ADB
* cletus\_mccoy\.android\_adb\.adb\_device\_state \- Manage Android device state over ADB
* cletus\_mccoy\.android\_adb\.adb\_forward \- Manage ADB port forwards for an Android device
* cletus\_mccoy\.android\_adb\.adb\_install \- Install an APK on an Android device via ADB
* cletus\_mccoy\.android\_adb\.adb\_intent \- Send an Android intent over ADB
* cletus\_mccoy\.android\_adb\.adb\_logcat \- Fetch Android logcat output over ADB
* cletus\_mccoy\.android\_adb\.adb\_packages \- List installed Android packages over ADB
* cletus\_mccoy\.android\_adb\.adb\_pair \- Pair with an Android device over ADB wirelessly
* cletus\_mccoy\.android\_adb\.adb\_reboot \- Reboot an Android device via ADB
* cletus\_mccoy\.android\_adb\.adb\_screenrecord \- Record the screen of an Android device using ADB
* cletus\_mccoy\.android\_adb\.adb\_uninstall \- Uninstall an app from an Android device via ADB
